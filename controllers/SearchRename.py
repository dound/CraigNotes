import logging
import urllib

from google.appengine.api import memcache
from google.appengine.ext import webapp

from controller_functions import is_logged_in
from FormHandler import FormHandler, validate_string
from MakoLoader import MakoLoader
from models.User import User, MAX_FEED_NAME_LEN

GET_PARAMS = ('new_name', 'f', 'current_name')
REDIR_URL = '/?redir_to=/tracker&info=Please%20login%20to%20update%20rename%20one%20of%20your%searches.'

class SearchRename(FormHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('search_rename.html', request=self.request))

    def post(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)

        req = self.request
        errors = {}

        new_name = validate_string(req, errors, 'new_name', 'new search name', MAX_FEED_NAME_LEN)
        if not new_name:
            new_name = ''
        if len(errors):
            return self.redirect_to_self(GET_PARAMS, errors)

        # update the search name
        user = User.get_by_key_name(session['my_id'])
        if not user:
            logging.error('Unable to retrieve user record for a logged in user: %s' % session['my_id'])
            return self.redirect('/?err=The service is temporarily unavailable - please try again later.')
        feed_key = self.request.get('f')
        if feed_key not in user.feeds:
            return self.redirect("/tracker&err=You%20can't%20rename%20a%20search%20you%20aren't%20tracking.")
        for i in xrange(len(user.feeds)):
            if user.feeds[i] == feed_key:
                user.feed_names[i] = new_name
                break
        try:
            user.put()
        except:
            logging.error('Unable to update user record for logged in user: %s' % session['my_id'])
            return self.redirect('/tracker?err=The service is temporarily unavailable - please try again later.')

        # invalidate the memcache entry for this users' feeds if it exists
        mckey = "user-feeds:%s" % session['my_id']
        feed_infos = memcache.delete(mckey)

        # redirect the user to the feed page
        self.redirect('/view?t=newest&f=%s' % urllib.quote(feed_key))
