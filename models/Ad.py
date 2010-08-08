from google.appengine.ext import db

class Ad(db.Model):
    # primary key will be the Craiglist ID
    feeds = db.ListProperty(str, required=True, indexed=True) # elements are HASHES of the Feed's PK (Feed.hashed_id() values)
    title = db.StringProperty(required=True, indexed=False)
    desc = db.TextProperty(required=True)
    update_dt = db.DateTimeProperty(required=True, indexed=True)
    url = db.StringProperty(required=True, indexed=False)

    @property
    def cid(self):
        return self.key().id()

    def __repr__(self):
        return 'Ad(cid=%s title=%s updated=%s feeds=%s)' % (self.cid, self.title, self.update_dt, self.feeds)
