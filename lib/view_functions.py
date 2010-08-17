import datetime
import hashlib
from math import log10

from mako.filters import html_escape, url_escape

from settings import DOMAIN

def format_float(n, max_dec_places=2):
    """Returns a string representation of the float n with up to max_dec_places decimal places."""
    sigfigs = 1 + max_dec_places + int(log10(n))
    fmt = '%%.%dg' % sigfigs
    return fmt % round(n, max_dec_places)

def format_date(dt):
    return dt.strftime('%A %B %%d, %Y') % dt.day

YUI3_LIBS = '3.1.1/build/' + '-min.js&amp;3.1.1/build/'.join([
    'yui/yui',
    'oop/oop',
    'event-custom/event-custom',
    'event/event-base',
    'event/event-key',
    'json/json-parse',
    'querystring/querystring-stringify-simple',
    'io/io-base',
    'dom/dom-base',
    'dom/selector-native',
    'dom/selector-css2',
    'node/node-base',
    'node/node-style',
    ]) + '-min.js&amp;'
YUI2IN3_LIBS = '2in3.1/2.8.0/build/' + '-min.js&amp;2in3.1/2.8.0/build/'.join([
    'yui2-calendar/yui2-calendar',
    'yui2-yahoo/yui2-yahoo',
    'yui2-dom/yui2-dom',
    'yui2-event/yui2-event',
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

def make_user_header_html(user_is_logged_in, session, path):
    """Returns the HTML to use for the user info portion of the header bar."""
    if not user_is_logged_in:
        return '<a href="/?redir_to=%s">login</a>' % path
    else:
        return '&nbsp; logged in as ' + html_escape(session['my_dname']) + ' | <a href="/logout">logout</a>'
