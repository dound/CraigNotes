from google.appengine.ext import db

from models.User import UID_LEN

MIN_RATING = 0
MAX_RATING = 5

class UserCmt(db.Model):
    # primary key will User ID + Craiglist ID
    feeds = db.ListProperty(str, required=True, indexed=True) # denormalized copy of the related Ad
    rating = db.IntegerProperty(required=True, indexed=True, default=0)
    cmt = db.TextProperty(required=False, default='')
    hidden = db.BooleanProperty(required=True, indexed=True, default=False)

    @property
    def uid(self):
        return self.key().name()[:UID_LEN]

    @property
    def cid(self):
        return int(self.key().name()[UID_LEN:])

    def __repr__(self):
        return 'UserCmt(uid=%s, cid=%s rating=%s hidden=%s)' % \
               (self.uid, self.cid, self.rating, self.hidden)
