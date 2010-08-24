import time
import urllib

from google.appengine.ext import db

from django.utils import simplejson
from google.appengine.api import urlfetch
from google.appengine.ext import webapp

from gaesessions import get_current_session

from models.User import User

class AnonLogin(webapp.RequestHandler):
    def get(self):
        # doesn't make sense if the user is already logged in
        session = get_current_session()
        if session.is_active():
            return self.redirect('/tracker?err=You%20are%20already%20logged%20in.')

        # get a unique ID for the anonymous user
        str_id = str(db.allocate_ids(db.Key.from_path('User', 1), 1)[0])
        hashed_id = User.make_key_name(str_id, anon=True)
        user = User.get_or_insert(key_name=hashed_id, display_name='anonymous', email='')

        # start a session for the user
        session['my_dname'] = user.display_name
        session['my_id'] = hashed_id
        session['my_last_seen'] = int(time.mktime(user.last_seen.timetuple()))
        session['my_email'] = user.email

        self.redirect('/tracker')
