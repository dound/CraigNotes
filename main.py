from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import fix_path
from gaesessions import SessionMiddleware
from LazyControllerLoader import url_list
import settings

class Warmup(webapp.RequestHandler):
    """This handler warms up the instance (imports modules, etc.)."""
    def get(self):
        pass

url_mappings = [
    ('.*',                     'controllers.Home.Home'),
    ]
app = webapp.WSGIApplication(url_list(url_mappings), debug=settings.DEBUG)

if settings.USE_APP_STATS:
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)

def main():
    fix_path.fix_sys_path()
    run_wsgi_app(app)

if __name__ == '__main__':
    main()
