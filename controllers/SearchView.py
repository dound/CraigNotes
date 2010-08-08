from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db, webapp

from controller_functions import is_logged_in
from MakoLoader import MakoLoader
from models.Ad import Ad
from models.Feed import Feed
from models.UserCmt import UserCmt

ADS_PER_PAGE = 25

class SearchView(webapp.RequestHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)
        feed_key_name = self.request.get('f')
        if not feed_key_name:
            return self.redirect('/tracker')

        # **transactionally** get the feed, and check to see if it needs to be
        # updated.  If it needs to be updated and it isn't marked as updating,
        # then set updating=True and enqueue a task to perform the update.  This
        # ensures a feed is only updated by one task at a time.
        def txn():
            feed = Feed.get_by_key_name(feed_key_name)
            if not feed:
                return None
            if feed.needs_update():
                if not feed.updating:
                    feed.updating = True
                    feed.put()
                    # enqueue a task to do the updating
                    taskqueue.add(url='/task/update_feed?f=%s'%feed_key_name, transactional=True)
                return True
            return False
        updating = db.run_in_transaction(txn)
        if updating is None:
            return self.redirect('/tracker?err=The%20requested%20feed%20does%20not%20exist.')

        # get ads associated with this feed
        fhid = feed.hashed_id()
        q = Ad.all().filter('feeds =', fhid)
        next = self.request.get('next')
        if next:
            q.with_cursor(self.request.get())
        ads = q.fetch(ADS_PER_PAGE)
        more = (len(ads) == ADS_PER_PAGE)

        # get user comments on these ads, if any
        uid = session['my_id']
        user_ad_keys = [db.Key.from_path('UserCmt', '%s%s' % (uid, a.cid)) for a in ads]
        user_ad_notes = db.get(user_ad_keys)
        ad_infos = zip(ads, user_ad_notes)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('view.html', request=self.request, ads=ad_infos, more=more))
