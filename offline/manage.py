#!/usr/bin/env python2.5
"""This script performs the following pre-deployment tasks:
    1) Pre-compile Mako templates.

It can also be used to deploy the app or run it on the local dev server.  When
running on the dev server, any changes to the templates will be automatically
re-compiled.  The dev server does not do app caching, so the new templates will
be auotmatically loaded by the dev server."""

from optparse import OptionParser
from os import mkdir
from os.path import abspath, dirname, exists
from shutil import rmtree
from StringIO import StringIO
from subprocess import Popen, PIPE, STDOUT
import fcntl
import os
import posixpath
import signal
import stat
import sys
import time

# check python version: must be 2.5 so GAE can execute the python mako generates
if sys.version_info[0]!=2 or sys.version_info[1]!=5:
    print "You must use python2.5 to use manage.py"
    sys.exit(-1)

APP_ROOT_PATH = dirname(abspath(__file__)) + '/../'
SOURCE_TEMPLATE_PATH = APP_ROOT_PATH + 'offline/templates/'
COMPILED_TEMPLATE_PATH = APP_ROOT_PATH + 'compiled_templates/'
PATH_TO_YUI_COMPRESSOR = APP_ROOT_PATH + 'offline/tools/yuicompressor-2.4.2.jar'

# update the path to include libraries from our project and GAE
APP_LIB_PATH = APP_ROOT_PATH + 'lib'
GAE_PATH = '/usr/local/google_appengine'
YAML_LIB_PATH = GAE_PATH + '/lib/yaml/lib'
sys.path.insert(0, APP_LIB_PATH)
sys.path.insert(0, GAE_PATH)
sys.path.insert(0, YAML_LIB_PATH)

import mako.template

PID_FILE = ".dev_appserver.pid"

def _copy_files(files, src_path, dst_path, minify):
    """Copies each filename in files from src_path to dst_path, minifying if minify is True."""
    for f in files:
        fp = open(src_path+f, 'r')
        code = fp.read()
        fp.close()
        if minify:
            print 'minifying ' + f
            if f[-2] == 'js':
                code = minify_js(code)
            else:
                code = minify_css(code)
        fp = open(dst_path+f, 'w')
        fp.write(code)
        fp.close()
        print 'copied ' + f
JS_FILES = ['view.js']
CSS_FILES = ['base.css']
def copy_js(minify):
    minify = False  # TODO, tmp
    _copy_files(JS_FILES, 'offline/js/', 'static/js/', minify)
def copy_css(minify):
    _copy_files(CSS_FILES, 'offline/css/', 'static/css/', minify)

def precompile_mako_templates(minify, watch=True):
    """Delete any existed compiled templates and then compile new ones.  All
    templates in SOURCE_TEMPLATE_PATH will be compiled to
    COMPILED_TEMPLATE_PATH.  If watch is True, then template source folders will
    be watched for changes and all templates will be recompiled if a chance
    occurs."""
    if exists(COMPILED_TEMPLATE_PATH):
        rmtree(COMPILED_TEMPLATE_PATH)
    mkdir(COMPILED_TEMPLATE_PATH)
    compile_templates(SOURCE_TEMPLATE_PATH, COMPILED_TEMPLATE_PATH, minify, watch=watch)
    print 'done compiling templates!'

def compile_templates(root, output, minify, input_encoding='utf-8', watch=True):
    """Compile all templates in root or root's subfolders."""
    root = posixpath.normpath(root)
    root_len = len(root)
    output = posixpath.normpath(output)
    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = posixpath.normpath(dirpath)
        if posixpath.basename(dirpath).startswith('.'): continue
        filenames = [f for f in filenames if not f.startswith('.') and not f.endswith('~') and not f.endswith('.py') and not f.endswith('.pyc')]
        outdir = posixpath.join(output , dirpath[root_len:])
        if not posixpath.exists(outdir):
            os.makedirs(outdir)
        if not posixpath.exists(posixpath.join(outdir, '__init__.py')):
            out = open(posixpath.join(outdir, '__init__.py'), 'w')
            out.close()
        for f in filenames:
            path = posixpath.join(dirpath, f).replace('\\','/')
            outfile = posixpath.join(outdir, f.replace('.','_')+'.py')
            filemtime = os.stat(path)[stat.ST_MTIME]
            if not exists(outfile) or os.stat(outfile)[stat.ST_MTIME] < filemtime:
                uri = path[root_len+1:]
                print 'compiling', uri
                text = file(path).read()
                if minify:
                    text = minify_js_in_html(uri, text)
                t = mako.template.Template(text=text, filename=path, uri=uri, input_encoding=input_encoding)
                out = open(outfile, 'w')
                out.write( t.code)
                out.close()
        if watch:
            watch_folder_for_changes(dirpath, minify)

def watch_folder_for_changes(path, minify):
    """Watch a folder for changes and call precompile_mako_templates() if a
    change occurs."""
    return # don't do this for now
    def handler(signum, frame):
        print "%s modified" % (path,)
        precompile_mako_templates(minify, watch=False)

    signal.signal(signal.SIGIO, handler)
    fd = os.open(path, os.O_RDONLY)
    fcntl.fcntl(fd, fcntl.F_SETSIG, 0)
    fcntl.fcntl(fd, fcntl.F_NOTIFY, fcntl.DN_MODIFY | fcntl.DN_CREATE | fcntl.DN_DELETE | fcntl.DN_RENAME)

JS_START_TAG = '<script type="text/javascript">'
JS_END_TAG = '</script>'
def minify_js_in_html(fn, text):
    """Uses the YUI compressor to replace any inline javascript with minified JS."""
    start_index = text.find(JS_START_TAG)
    while start_index != -1:
        end_index = text.find(JS_END_TAG, start_index)
        if end_index == -1:
            raise Exception('missing end script tag!')

        js = text[start_index+len(JS_START_TAG):end_index]
        js_min = minify_js(js)
        text = text[:start_index+len(JS_START_TAG)] + js_min + text[end_index:]

        # look for another block of inline JS
        start_index = text.find(JS_START_TAG, start_index+len(JS_START_TAG)+len(js_min)+len(JS_END_TAG))
    return text

def _minify(code, type):
    """Takes JavaScript code and returns a minified version."""
    p = Popen(['java', '-jar', PATH_TO_YUI_COMPRESSOR, '--type', type], stdin=PIPE, stdout=PIPE)
    code_min = p.communicate(code)[0]
    sz_old, sz_new = len(code), len(code_min)
    sz_saved = sz_old - sz_new
    print 'minified %dB of %s to %dB => %.2f%% savings (%dB)' % (sz_old, type, sz_new, sz_saved*100.0/sz_old, sz_saved)
    return code_min
def minify_js(js):
    return _minify(js, 'js')
def minify_css(css):
    return _minify(css, 'css')

def main(argv=sys.argv[1:]):
    """Parses the command line comments and runs the program."""
    usage = 'usage: %prog [options]\n\n' + __doc__
    parser = OptionParser(usage)

    # options
    parser.add_option("-d", "--deploy",
                      action='store_true', default=False,
                      help="deploy to the production GAE servers")
    parser.add_option("-m", "--minify",
                      action='store_true', default=False,
                      help="minify inline JS in templates (always done if -d is specified)")
    parser.add_option("-r", "--run",
                      action='store_true', default=False,
                      help="run on the local development server")

    (options, args) = parser.parse_args(argv)
    if len(args) != 0:
        parser.error("expected 0 arguments but got %d argument(s): %s" % (len(args), ' '.join(args)))

    minify = options.deploy or options.minify
    precompile_mako_templates(minify)
    copy_js(minify)
    copy_css(minify)
    if options.run:
        if options.deploy:
            print 'ignoring --deploy ... will just run the local dev server as requested'

        # run the dev server, stopping the running app server if any
        dev_app_server_args = ['/usr/local/google_appengine/dev_appserver.py', '--datastore_path', './clb-dev.db', APP_ROOT_PATH]
        try:
            p = Popen(dev_app_server_args)
        except:
            try:
                fp_pid_to_kill = open(PID_FILE, "r")
                pid_to_kill = int(fp_pid_to_kill.readline())
                fp_pid_to_kill.close()
                Popen(['kill', pid_to_kill])
                p = Popen(dev_app_server_args)
            except:
                print 'Unable to stop the old server'
                return

        # note the PID of the dev server process in a file
        fp_pid = open(PID_FILE, "w")
        print >> fp_pid, p.pid
        fp_pid.close()

        # wait for it to stop or for a Ctrl-C
        try:
            p.wait()
        except KeyboardInterrupt:
            print 'Ctrl-C received, stopping the server ...'
            Popen(['kill', str(p.pid)]).wait()
    elif options.deploy:
        p = Popen(['appcfg.py', 'update', APP_ROOT_PATH])
        p.wait()

if __name__ == '__main__': main()
