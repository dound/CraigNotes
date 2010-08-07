import datetime
import hashlib
import time

from google.appengine.api import memcache
from google.appengine.ext import db

UID_LEN = 20

class User(db.Model):
    # primary key will be the SHA1 of the user's OpenID identifier
    display_name    = db.StringProperty(required=True,   indexed=False)
    email           = db.StringProperty(required=False,  indexed=True)
    date_registered = db.DateTimeProperty(required=True, indexed=False, auto_now_add=True)
    last_seen       = db.DateTimeProperty(required=True, indexed=False, auto_now_add=True)
    reputation      = db.IntegerProperty(required=True , indexed=True,  default=0)

    @staticmethod
    def make_key_name(oid):
        m = hashlib.sha1(oid)
        m.update('$#%119nD23') # SALT
        return m.hexdigest()[:UID_LEN]

    def hashed_id(self):
        """Returns the key_name associated with this User."""
        return self.key().name()

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
        return 'User(uid=%s dname=%s email=%s gender=%s last_seen=%s rep=%s date_reg=%s)' % (self.hashed_id(), self.display_name, self.email, self.gender, self.last_seen, self.reputation, self.date_registered)

USER_NAME_CACHE = {}
def get_user_name(uid):
    """Returns the user display name associated with the specified uid.
    The information is looked up from the datastore if it isn't cached in
    memcache or in the local app's cache.
    """
    now = time.time()
    try:
        timeout, user_name = USER_NAME_CACHE[uid]
        if timeout > now:
            del USER_NAME_CACHE[uid]
        else:
            return user_name
    except KeyError:
        pass

    # try to get the name from memcache
    mckey = 'username:%s' % uid
    user_name = memcache.get(mckey)
    if user_name is None:
        # not in cache: try to get from datastore
        user = User.get_by_key_name(uid)
        if user:
            # got from datastore; save in cache for next time
            user_name = user.display_name
            memcache.set(mckey, user_name, 60)
            USER_NAME_CACHE[uid] = (now+60, user_name)
        else:
            logging.warn("could not find the requested user (uid=%s)" % uid)
            user_name = 'unknown'
    return user_name
