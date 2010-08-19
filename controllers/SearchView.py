import datetime

from google.appengine.api import memcache
from google.appengine.ext import db, webapp

from controller_functions import is_logged_in
from MakoLoader import MakoLoader
from models.Ad import Ad
from models.Feed import Feed, dt_feed_last_updated, update_feed_if_needed, MAX_AGE_MIN
from models.UserCmt import UserCmt
from view_functions import str_age

ADS_PER_PAGE = 25

class SearchView(webapp.RequestHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)
        uid = session['my_id']

        feed_key_name = self.request.get('f')
        if not feed_key_name:
            return self.redirect('/tracker')
        fhid = Feed.hashed_id_from_pk(feed_key_name)

        # compute how old the data is
        feed_dt_updated = dt_feed_last_updated(feed_key_name)
        if not feed_dt_updated:
            return self.redirect('/tracker?err=That%20feed%20no%20longer%20exists.')
        now = datetime.datetime.now()
        age = str_age(feed_dt_updated, now)
        td = now - feed_dt_updated
        if td.days>0 or td.seconds>15*60:
            age += ' - will update shortly'

        # update the feed if we haven't retrieved the latest ads recently
        updating = update_feed_if_needed(feed_key_name)
        if updating is None:
            return self.redirect('/tracker?err=The%20requested%20feed%20does%20not%20exist.')

        # determine which set of ads to show
        next = self.request.get('next')
        t = self.request.get('t')
        if t == 'newest':
            # show the newest ads (regardless of whether the user has commented on them or not)
            q = Ad.all().filter('feeds =', fhid).order('-update_dt')
            if next:
                q.with_cursor(next)
            ads = q.fetch(ADS_PER_PAGE)

            # get user comments on these ads, if any
            user_ad_keys = [db.Key.from_path('UserCmt', '%s%s' % (uid, a.cid)) for a in ads]
            user_ad_notes = db.get(user_ad_keys)
            title_extra = 'Newest Ads'
        else:
            # show ads this user has commented on/rated (whether to show hidden ads or not depends on t)
            q = UserCmt.all().filter('feeds =', fhid).filter('hidden =', t=='hidden').order('-rating')
            if next:
                q.with_cursor(next)
            user_ad_notes = q.fetch(ADS_PER_PAGE)

            # get the ads associated with these comments
            ad_keys = [db.Key.from_path('Ad', uan.cid) for uan in user_ad_notes]
            ads = db.get(ad_keys)

            if t == 'hidden':
                title_extra = "Ads I've Rated"
            else:
                title_extra = "Ignored Ads"


        # put the ads and their comments together
        ad_infos = zip(ads, user_ad_notes)

        # whether there may be more ads
        more = (len(ads) == ADS_PER_PAGE)
        if more:
            more = q.cursor()
        if not more or more==str(next):
            more = None

        # get a description of the search we're viewing
        tmp_feed = Feed(key_name=feed_key_name)
        tmp_feed.extract_values()
        desc = tmp_feed.desc()

        if not next:
            page = 1
        else:
            try:
                page = int(self.request.get('page', 1))
            except ValueError:
                page = 1;

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('search_view.html', request=self.request,
                                                  ads=ad_infos, more=more, age=age, now=now, search_desc=desc, title_extra=title_extra, page=page))
