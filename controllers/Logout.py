from google.appengine.ext import webapp

from gaesessions import get_current_session

class Logout(webapp.RequestHandler):
    def get(self):
        get_current_session().terminate()
        self.redirect('/')
