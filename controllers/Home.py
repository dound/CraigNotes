from google.appengine.ext import webapp

from gaesessions import get_current_session
from MakoLoader import MakoLoader
from settings import DOMAIN

class Home(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.headers['Cache-Control'] = 'max-age=86400, public'
        self.response.out.write(MakoLoader.render('shutdown.html', request=self.request))
