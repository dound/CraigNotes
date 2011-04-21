from google.appengine.ext import db

from aetycoon import DerivedProperty
from models.User import UID_LEN

MIN_RATING = 0
MAX_RATING = 5
MAX_NOTE_LEN = 1024 * 32

class UserCmt(db.Expando):
    # primary key will User ID + Craiglist ID
    feeds = db.ListProperty(str, required=True, indexed=True) # denormalized copy of the related Ad
    rating = db.IntegerProperty(required=True, indexed=True, default=0)
    cmt = db.TextProperty(required=False, default='')
    dt_hidden = db.DateTimeProperty(required=False, indexed=True)  # None if not hidden

    @DerivedProperty(required=False, indexed=True)
    def uid(self):
        return self.key().name()[:UID_LEN]

    @property
    def cid(self):
        return int(self.key().name()[UID_LEN:])

    @property
    def hidden(self):
        return self.dt_hidden is not None

    def __repr__(self):
        return 'UserCmt(uid=%s, cid=%s rating=%s dt_hidden=%s)' % \
               (self.uid, self.cid, self.rating, self.dt_hidden)
