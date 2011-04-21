import datetime
import hashlib
import logging
import time

from google.appengine.api import memcache
from google.appengine.ext import db

from controller_functions import is_logged_in
from models.Feed import Feed

MAX_FEED_NAME_LEN = 30
UID_LEN = 20

class User(db.Model):
    # primary key will be the SHA1 of the user's OpenID identifier
    display_name    = db.StringProperty(required=True,   indexed=False)
    email           = db.StringProperty(required=False,  indexed=True)
    date_registered = db.DateTimeProperty(required=True, indexed=False, auto_now_add=True)
    last_seen       = db.DateTimeProperty(required=True, indexed=False, auto_now_add=True)
    feeds           = db.ListProperty(str, indexed=False)  # key_names of feeds the user is watching
    feed_names      = db.ListProperty(str, indexed=False)  # user-specified names of feeds the user is watching

    @staticmethod
    def make_key_name(oid, anon=False):
        """All and only anonymous accounts are prefixed with a 'Z'."""
        m = hashlib.sha1(oid)
        m.update('mr#9S$98K') # SALT
        if anon:
            return 'Z' + m.hexdigest()[:UID_LEN-1]
        else:
            return m.hexdigest()[:UID_LEN]

    def hashed_id(self):
        """Returns the key_name associated with this User."""
        return self.key().name()

    def is_anon(self):
        """Returns True if this User is anonymous (not logged in via RPX)."""
        return self.hashed_id()[0]=='Z'

    @staticmethod
    def note_user_activity(key_name, last_seen):
        """Updates User.last_seen if it hasn't been updated in over an hour.
        @param key_name   the key for the User who has just accessed a page
        @param last_seen  UNIX timestamp stored in the user's last_seen field

        @return  None if no change was saved, otherwise a new timestamp is returned.  False if key_name is bad.
        """
        now = int(time.time())
        if last_seen+3600 < now:
            user = User.get_by_key_name(key_name)
            if not user:
                return False
            user.last_seen = datetime.datetime.now()
            user.put()
            return now
        return None

    def __repr__(self):
        return 'User(uid=%s dname=%s email=%s last_seen=%s date_reg=%s)' % (self.hashed_id(), self.display_name, self.email, self.last_seen, self.date_registered)

def get_feed_infos(handler):
    """Returns an array of 2-tuples (feed_name, feed_key) for the current user,
    or False on failure.
    """
    session = is_logged_in(handler)
    if not session:
        return False
    uid = session['my_id']

    mckey = "user-feeds:%s" % uid
    feed_infos = memcache.get(mckey)
    if not feed_infos:
        user = User.get_by_key_name(uid)
        if not user:
            logging.error('cannot find the profile for a logged in user (%s)' % uid)
            session.terminate()
            return False
        feed_keys = [db.Key.from_path('Feed', f) for f in user.feeds]
        if feed_keys:
            feeds = db.get(feed_keys)
        else:
            feeds = []
        feed_infos = zip(user.feed_names, feeds)
        memcache.set(mckey, feed_infos, 30*60)
    return feed_infos

def get_search_name(handler, feed_key_name):
    """Returns what the user has named the feed with the specified name.  If the
    user is not logged in or an error occurs, False is returned.  If the user is
    not watching a feed with this key then None is returned.
    """
    feed_infos = get_feed_infos(handler)
    if not feed_infos:
        return False
    for name,feed in feed_infos:
        if feed.key().name() == feed_key_name:
            return name
    return None
