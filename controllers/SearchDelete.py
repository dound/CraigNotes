from google.appengine.api import memcache
from google.appengine.ext import webapp

from controller_functions import is_logged_in
from models.User import User

class SearchDelete(webapp.RequestHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)
        feed_key_name = self.request.get('f')
        if not feed_key_name:
            return self.redirect('/tracker')

        # remove the feed from this user's record
        user = User.get_by_key_name(session['my_id'])
        n = len(user.feeds)
        user.feeds = [f for f in user.feeds if f!=feed_key_name]
        user.put()
        if n > len(user.feeds):
            self.redirect('/tracker?info=Success', 30*60)

            # clear the memcache entry for this users' feeds
            mckey = "user-feeds:%s" % session['my_id']
            memcache.delete(mckey)
        else:
            self.redirect('/tracker?info=The%20feed%20you%20asked%20to%20stop%20tracking%20was%20not%20being%20tracked.')
