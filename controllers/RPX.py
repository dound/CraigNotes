import time
import urllib

from django.utils import simplejson
from google.appengine.api import memcache, urlfetch
from google.appengine.ext import db, webapp

from gaesessions import get_current_session

from models.User import User, get_feed_infos
from models.UserCmt import UserCmt

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
        old_uid = old_feed_infos = None
        if session.is_active():
            old_uid = session.get('my_id', 'x')
            if old_uid[0] == 'Z':
                old_feed_infos = get_feed_infos(None)
            session.terminate()

        redir_to = self.request.get('redir_to')
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

            # if the user was logged in anonymously, merge their info into this account
            more = ''
            if old_uid and old_uid[0] == 'Z':
                # 1) Add User.feeds and feed_names into this User
                old_feed_infos = [(of_name, of_feed.key().name()) for of_name, of_feed in old_feed_infos]
                new_feed_infos = zip(user.feed_names, user.feeds)
                changed = False
                for ofi in old_feed_infos:
                    if ofi not in new_feed_infos:
                        new_feed_infos.append(ofi)
                        changed = True
                if changed:
                    tfn, tf = zip(*new_feed_infos)
                    user.feed_names, user.feeds = list(tfn), list(tf)
                    user.put()
                    # clear memcache for this user since the value is stale if present
                    memcache.delete("user-feeds:%s" % hashed_id)

                # 2) Get the UserCmt for old_uid and move them to the logged in user account
                if old_feed_infos:
                    start_key, end_key = db.Key.from_path('UserCmt', old_uid), db.Key.from_path('UserCmt', old_uid+'\ufffd')
                    old_cmts = UserCmt.all().filter('__key__ >', start_key).filter('__key__ <', end_key).fetch(250)
                    new_cmts = [UserCmt(key_name='%s%s'%(hashed_id,cmt.cid), feeds=cmt.feeds, rating=cmt.rating, cmt=cmt.cmt, dt_hidden=cmt.dt_hidden) for cmt in old_cmts]
                    db.put(new_cmts)
                    db.delete(old_cmts)
                    if len(new_cmts) == 250:
                        more = '?info=We%20merged%20250%20comments%20so%20far%20and%20we%20will%20finish%20the%20rest%20soon.'
                        logging.error('Need to finish converting anonymous comments by uid %s to %s' % (old_uid, hashed_id))
                        # TODO: do this on the task queue instead of just raising an error

            if not redir_to or more:
                self.redirect('/tracker' + more)
            else:
                self.redirect(redir_to.replace('@$@', '&'))
        else:
            msg = json['err']['msg']
            if not redir_to:
                qp = dict(login_error=msg)
            else:
                qp = dict(login_error=msg, redir_to=redir_to)
            self.redirect('/?' + urllib.urlencode(qp))
