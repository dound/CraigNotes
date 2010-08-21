import datetime

from google.appengine.api import memcache
from google.appengine.ext import db, webapp

from controller_functions import is_logged_in
from MakoLoader import MakoLoader
from models.Ad import Ad
from models.Feed import Feed, dt_feed_last_updated, update_feed_if_needed, MAX_AGE_MIN
from models.User import get_search_name
from models.UserCmt import UserCmt
from view_functions import str_age

ADS_PER_PAGE = 25
DT_PRESITE = datetime.datetime(2000, 1, 1)  # arbitrary date preceding this site

class SearchView(webapp.RequestHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)
        uid = session['my_id']

        now = datetime.datetime.now()
        feed_key_name = self.request.get('f')
        t = self.request.get('t')
        overall_view = (not feed_key_name and t != 'newest')
        if feed_key_name:
            fhid = Feed.hashed_id_from_pk(feed_key_name)

            # get the user's name for this feed
            name = get_search_name(self, feed_key_name)
            if name is None:
                return self.redirect('/tracker')  # user is no longer tracking this feed
            elif name is False:
                return self.redirect('/') # login related error

            # compute how old the data is
            feed_dt_updated = dt_feed_last_updated(feed_key_name)
            if not feed_dt_updated:
                return self.redirect('/tracker?err=That%20feed%20no%20longer%20exists.')
            age = str_age(feed_dt_updated, now)
            td = now - feed_dt_updated
            updating_shortly = td.days>0 or td.seconds>MAX_AGE_MIN*60
            if updating_shortly:
                age += ' - update in progress'

            # update the feed if we haven't retrieved the latest ads recently
            updating = update_feed_if_needed(feed_key_name)
            if updating is None:
                return self.redirect('/tracker?err=The%20requested%20feed%20does%20not%20exist.')
        elif overall_view:
            age = desc = fhid = None
            updating_shortly = False
            if t == 'hidden':
                name = "All Hidden Ads"
            else:
                name = "All Rated/Noted Ads"
        else:
            # t=newest and feed=all doesn't make sense together
            return self.redirect('/tracker')

        # determine which set of ads to show
        next = self.request.get('next')
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
            hidden = (t == 'hidden')
            q = UserCmt.all()
            if fhid:
                q.filter('feeds =', fhid)
            if hidden:
                q.filter('dt_hidden >', DT_PRESITE).order('-dt_hidden')
            else:
                q.filter('dt_hidden =', None).order('-rating')
            if next:
                q.with_cursor(next)
            user_ad_notes = q.fetch(ADS_PER_PAGE)

            # get the ads associated with these comments
            ad_keys = [db.Key.from_path('Ad', uan.cid) for uan in user_ad_notes]
            ads = db.get(ad_keys)

            if t == 'hidden':
                title_extra = "Ignored Ads"
            else:
                title_extra = "Ads I've Rated"

        # put the ads and their comments together
        ad_infos = zip(ads, user_ad_notes)

        # check that each UserCmt.feeds field is up to date with Ad.feeds (can
        # only do this when we're searching by Ad, i.e., t=newest)
        if t == 'newest':
            outdated = [(ad,cmt) for ad, cmt in ad_infos if cmt and ad.feeds!=cmt.feeds]
            if outdated:
                # update any out of date comments
                for ad,cmt in outdated:
                    cmt.feeds = ad.feeds
                db.put([cmt for ad,cmt in outdated])

        # whether there may be more ads
        more = (len(ads) == ADS_PER_PAGE)
        if more:
            more = q.cursor()
        if not more or more==str(next):
            more = None

        # get a description of the search we're viewing
        if fhid:
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
                                                  ADS_PER_PAGE=ADS_PER_PAGE, ads=ad_infos, more=more, age=age, now=now, search_desc=desc, title_extra=title_extra, page=page, name=name, updating_shortly=updating_shortly, overall_view=overall_view))
