from google.appengine.ext import webapp

from gaesessions import get_current_session
from MakoLoader import MakoLoader
from settings import DOMAIN

class Home(webapp.RequestHandler):
    def get(self):
        session = get_current_session()
        if session.has_key('my_id'):
            redir_to = self.request.get('redir_to')
            if redir_to:
                self.redirect(redir_to)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('index.html', request=self.request, base_url=DOMAIN))
