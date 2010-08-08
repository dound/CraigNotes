from google.appengine.ext import db

from models.User import UID_LEN

class UserCmt(db.Model):
    # primary key will User ID + Craiglist ID
    feeds = db.ListProperty(str, required=True, indexed=True) # denormalized copy of the related Ad
    rating = db.IntegerProperty(required=True, indexed=True)
    cmt = db.TextProperty(required=True)
    ignored = db.BooleanProperty(required=True, indexed=True)

    @property
    def uid(self):
        return self.key().name()[:UID_LEN]

    @property
    def cid(self):
        return int(self.key().name()[UID_LEN:])

    def __repr__(self):
        return 'UserCmt(uid=%s, cid=%s rating=%s ignored=%s)' % \
               (self.uid, self.cid, self.rating, self.ignored)
