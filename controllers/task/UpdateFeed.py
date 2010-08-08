from google.appengine.ext import webapp

from MakoLoader import MakoLoader

class UpdateFeed(webapp.RequestHandler):
    def get(self, template_name):
        # TODO: update memcache key which specifies when a feed was last updated
        pass
