import datetime
import hashlib
from math import log10

from mako.filters import html_escape, url_escape

from settings import DOMAIN

def str_age(a, now):
    td = now - a
    if td.days > 365:
        return 'never'
    elif td.days > 0:
        if td.days > 1:
            return '%d days ago' % td.days
        else:
            return '1 day ago'
    elif td.seconds >= 3540: # 59 minutes
        h = ((td.seconds+60)/3600)
        if h > 1:
            return '%d hours ago' % h
        else:
            return '1 hour ago'
    else:
        m = (td.seconds/60 + 1)
        if m > 1:
            return 'less than %d minutes ago' % m
        else:
            return 'less than 1 minute ago'

def format_float(n, max_dec_places=2):
    """Returns a string representation of the float n with up to max_dec_places decimal places."""
    sigfigs = 1 + max_dec_places + int(log10(n))
    fmt = '%%.%dg' % sigfigs
    return fmt % round(n, max_dec_places)

def format_date(dt):
    return dt.strftime('%A %B %%d, %Y') % dt.day

YUI3_LIBS = '3.1.1/build/' + '-min.js&amp;3.1.1/build/'.join([
    'yui/yui',
    'event/event-base',
    'event/event-key',
    'event-custom/event-custom-base',  # required by io/io-base
    'io/io-base',
    'oop/oop',                         # required by dom/dom
    'dom/dom',
    'node/node-base',
    'node/node-style',
    ]) + '-min.js&amp;'
YUI2IN3_LIBS = '2in3.1/2.8.1/build/' + '-min.js&amp;2in3.1/2.8.1/build/'.join([
    'yui2-yahoo/yui2-yahoo',
    'yui2-dom/yui2-dom',
    'yui2-event/yui2-event',
    'yui2-element/yui2-element',
    'yui2-editor/yui2-editor',
    'yui2-containercore/yui2-containercore',
    'yui2-menu/yui2-menu',
    'yui2-button/yui2-button',
    ]) + '-min.js'
YUI_SCRIPTS = '<script type="text/javascript" src="http://yui.yahooapis.com/combo?%s"></script>' % (YUI3_LIBS + YUI2IN3_LIBS)

def get_yui_script_tag():
    """Returns an HTML script tag which loads the YUI components we use."""
    return YUI_SCRIPTS

def make_js_cal_params(date, select_date=True):
    ret = ''
    if date:
        if select_date:
            ret = ',"selected":"%s"' % date
        try:
            dt = datetime.datetime.strptime(date, '%m/%d/%Y')
            ret += ',"pagedate":"%s"' % dt.date().strftime('%m/%Y')
        except:
            pass
    return ret
