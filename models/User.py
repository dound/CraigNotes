import datetime
import hashlib
import time

from google.appengine.ext import db

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
    def make_key_name(oid):
        m = hashlib.sha1(oid)
        m.update('mr#9S$98K') # SALT
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
