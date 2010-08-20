import logging

from google.appengine.api import memcache
from google.appengine.ext import db, webapp

from controller_functions import is_logged_in
from controllers.PageNotFound import PageNotFound
from MakoLoader import MakoLoader
from models.Feed import Feed
from models.User import User

class UserProfile(webapp.RequestHandler):
    def get(self):
        # must be logged in to view your profile
        session = is_logged_in(self)
        if not session:
            return self.redirect('/')
        uid = session['my_id']

        mckey = "user-feeds:%s" % uid
        feed_infos = memcache.get(mckey)
        if not feed_infos:
            user = User.get_by_key_name(uid)
            if not user:
                logging.error('cannot find the profile for a logged in user (%s)' % uid)
                session.terminate()
                return self.redirect('/')
            feed_keys = [db.Key.from_path('Feed', f) for f in user.feeds]
            if feed_keys:
                feeds = db.get(feed_keys)
            else:
                feeds = []
            feed_infos = zip(user.feed_names, feeds)
            memcache.set(mckey, feed_infos, 30*60)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('userprofile.html', request=self.request, feed_infos=feed_infos))
