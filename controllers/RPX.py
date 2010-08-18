import time
import urllib

from django.utils import simplejson
from google.appengine.api import urlfetch
from google.appengine.ext import webapp

from gaesessions import get_current_session

from models.User import User

class RPX(webapp.RequestHandler):
    """Receive the POST from RPX with our user's login information."""
    def post(self):
        token = self.request.get('token')
        url = 'https://rpxnow.com/api/v2/auth_info'
        args = {
            'format': 'json',
            'apiKey': '78383d7d2030d84d6df056d5cd3fb962c88f18a4',
            'token': token
        }
        r = urlfetch.fetch(url=url,
                           payload=urllib.urlencode(args),
                           method=urlfetch.POST,
                           headers={'Content-Type':'application/x-www-form-urlencoded'})
        json = simplejson.loads(r.content)

        # close any active session the user has since he is trying to login
        session = get_current_session()
        if session.is_active():
            session.terminate()

        if json['stat'] == 'ok':
            # extract some useful fields
            info = json['profile']
            oid = info['identifier']
            email = info.get('email', '')
            try:
                display_name = info['displayName']
            except KeyError:
                display_name = email.partition('@')[0]
            if not display_name:
                display_name = 'Unknown'

            # get the user's account (creating one if they did not previously have one)
            hashed_id = User.make_key_name(oid)
            user = User.get_or_insert(key_name=hashed_id, display_name=display_name, email=email)

            # start a session for the user
            session['my_dname'] = user.display_name
            session['my_id'] = hashed_id
            session['my_last_seen'] = int(time.mktime(user.last_seen.timetuple()))
            session['my_email'] = user.email

            redir_to = self.request.get('redir_to')
            if not redir_to:
                self.redirect('/')
            else:
                self.redirect(redir_to.replace('@$@', '&'))
        else:
            msg = json['err']['msg']
            self.redirect('/?' + urllib.urlencode(dict(login_error=msg, redir_to=redir_to)))
