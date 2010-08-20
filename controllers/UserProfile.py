import logging

from google.appengine.api import memcache
from google.appengine.ext import db, webapp

from MakoLoader import MakoLoader
from models.User import get_feed_infos

class UserProfile(webapp.RequestHandler):
    def get(self):
        feed_infos = get_feed_infos(self)
        if feed_infos is False:
            return self.redirect('/') # user not logged in, or error (handled already)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('userprofile.html', request=self.request, feed_infos=feed_infos))
