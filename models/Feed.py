import datetime
import hashlib
import urllib

from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db

CATEGORIES = {
    'ccc': 'all community',
    'eee': 'all event',
    'sss': 'all for sale / wanted',
    'ggg': 'all gigs',
    'hhh': 'all housing',
    'aap': 'all apartments',
    'nfa': 'all no fee apts',
    'hou': 'apts wanted',
    'apa': 'apts/housing for rent',
    'swp': 'housing swap',
    'hsw': 'housing wanted',
    'off': 'office &amp; commercial',
    'prk': 'parking &amp; storage',
    'reb': 'real estate - by broker',
    'reo': 'real estate - by owner',
    'rea': 'real estate for sale',
    'rew': 'real estate wanted',
    'roo': 'rooms &amp; shares',
    'sha': 'rooms wanted',
    'sbw': 'sublet/temp wanted',
    'sub': 'sublets &amp; temporary',
    'vac': 'vacation rentals',
    'jjj': 'all jobs',
    'ppp': 'all personals',
    'res': 'all resume',
    'bbb': 'all services offered'
}

CITIES = {
    'sandiego': 'San Diego',
    'sfbay': 'San Francisco / Bay Area'
}

FID_LEN = 20
MAX_AGE_MIN = 15
MAX_AGE = datetime.timedelta(minutes=MAX_AGE_MIN)

class Feed(db.Model):
    # primary key will contain URL query params which identify this feed
    last_update = db.DateTimeProperty(required=True, indexed=False, default=datetime.datetime(2000,1,1))
    updating = db.BooleanProperty(required=True, indexed=False, default=False)

    def extract_values(self):
        if hasattr(self, '_values'):
            return
        self._values = self.key().name().split('|', 10)
        if not self._values[8]:
            self._values[8] = []
        else:
            self._values[8] = self._values[8].split('+')

    def make_url(self, rss=True):
        url = 'http://%s.craigslist.org/search/%s?'
        d = {}
        if self.min_ask:
            d['minAsk'] = self.min_ask
        if self.max_ask:
            d['maxAsk'] = self.max_ask
        if self.num_bedrooms:
            d['bedrooms'] = self.num_bedrooms
        if self.allow_cats:
            d['addTwo'] = 'purrr'
        if self.allow_dogs:
            d['addThree'] = 'wooof'
        if self.pics_required:
            d['hasPic'] = '1'
        if self.search_type != 'A' and self.query:
            d['srchType'] = self.search_type
        if self.query:
            d['query'] = self.query
        if rss:
            d['format'] = 'rss'
        extra = ''.join('&nh=%s'%nh for nh in self.neighborhoods)
        return 'http://%s.craigslist.org/search/%s?%s%s' % (self.city, self.category, urllib.urlencode(d), extra)

    def put(self):
        if hasattr(self, 'values'):
            del self._values
        super(Feed, self).put()

    @property
    def hashed_id(self):
        return Feed.hashed_id_from_pk(self.key().name())

    @staticmethod
    def hashed_id_from_pk(pk):
        m = hashlib.sha1(pk)
        m.update('Su%jcc8W#') # SALT
        return m.hexdigest()[:FID_LEN]

    def needs_update(self):
        return (self.last_update + MAX_AGE) <= datetime.datetime.now()

    @property
    def city(self):
        return self._values[0]

    def city_str(self):
        cabbr = self._values[0]
        try:
            return CITIES[cabbr]
        except KeyError:
            return cabbr

    @property
    def category(self):
        return self._values[1]

    def category_str(self):
        cabbr = self._values[1]
        try:
            return CATEGORIES[cabbr]
        except KeyError:
            return cabbr

    @property
    def min_ask(self):
        return self._values[2]

    @property
    def max_ask(self):
        return self._values[3]

    def cost_str(self):
        if self.min_ask and self.max_ask:
            return '$%s-$%s' % (self.min_ask, self.max_ask)
        elif self.min_ask:
            return 'at least $%s' % self.min_ask
        elif self.max_ask:
            return 'no more than $%s' % self.max_ask
        else:
            return 'any'

    @property
    def num_bedrooms(self):
        return self._values[4]

    def bedrooms_str(self):
        if self.num_bedrooms == '':
            return '0+'
        else:
            return self.num_bedrooms

    @property
    def allow_cats(self):
        return self._values[5]=='c'

    @property
    def allow_dogs(self):
        return self._values[6]=='d'

    def pets_str(self):
        if self.allow_cats and self.allow_dogs:
            return 'cats and dogs OK'
        elif self.allow_cats:
            return 'cats only'
        elif self.allow_dogs:
            return 'dogs only'
        else:
            return 'any'

    def pets_str2(self):
        if self.allow_cats and self.allow_dogs:
            return 'cats and dogs allowed'
        elif self.allow_cats:
            return 'cats allowed'
        elif self.allow_dogs:
            return 'dogs allowed'
        else:
            return ''

    @property
    def pics_required(self):
        return self._values[7]=='d'

    @property
    def neighborhoods(self):
        return self._values[8]

    def neighborhoods_str(self):
        if self.neighborhoods:
            return ', '.join(n for n in self.neighborhoods)
        return 'Any'

    @property
    def search_type(self):
        return self._values[9]

    @property
    def query(self):
        return self._values[10]

    @staticmethod
    def make_key_name(city, category, min_ask, max_ask, num_bedrooms,
                      allow_cats, allow_dogs, pics, neighborhoods, search_type, query):
        if allow_cats:
            cats = 'c'
        else:
            cats = ''
        if allow_dogs:
            dogs = 'd'
        else:
            dogs = ''
        if pics:
            pics = '1'
        else:
            pics = ''
        if not query:
            search_type = ''
        nstrs = '+'.join(str(n) for n in neighborhoods)
        return '|'.join(str(s) for s in [city, category, min_ask, max_ask,
                                         num_bedrooms, cats, dogs, pics, nstrs,
                                         search_type, query])

    def desc(self):
        """Returns a string describing this object in a plain English format."""
        cs = self.cost_str()
        if cs != 'any':
            cs = ' which cost %s' % cs
        else:
            cs = ''
        ps = self.pets_str2()
        if ps != '':
            ps = '; %s' % ps
        s = '%s in %s for %s bedroom(s) places%s%s' % (
            self.category_str(), self.city_str(), self.bedrooms_str(), cs, ps)
        if self.query:
            s += '; search terms: %s' % self.query
            if self.search_type == 'T':
                s += ' (title search only)'
        if self.neighborhoods:
            s += '; neighborhoods: %s' % self.neighborhoods_str()
        return s

    def __repr__(self):
        return 'Feed(city=%s cat=%s $=%s-%s num_br=%s cats=%s dogs=%s neighbs=%s q_type=%s q=%s updated=%s)' % \
               (self.city, self.category, self.min_ask, self.max_ask, self.num_bedrooms, self.allow_cats, self.allow_dogs, self.neighborhoods, self.search_type, self.query, self.last_update)

def dt_feed_last_updated(feed_key_name):
    """Returns the datetime when the specified feed was last updated.  This
    value is cached so that it doesn't always have to read from the datastore.
    """
    mc_key = 'feed-update-dt:%s' % feed_key_name
    dt = memcache.get(mc_key)
    if not dt:
        feed = Feed.get_by_key_name(feed_key_name)
        if not feed:
            return None
        else:
            dt = feed.last_update
            memcache.set(mc_key, dt)
    return dt

def update_feed_if_needed(feed_key_name):
    """**Transactionally** get the feed, and check to see if it needs to be
    updated.  If it needs to be updated and it isn't marked as updating, then
    set updating=True and enqueue a task to perform the update.  This ensures a
    feed is only updated by one task at a time.

    Returns None if no such feed exists.  Return True if the feed is being
    updated, and False if the feed is up to date.
    """
    # optimization: memcache lock lasts until we need to update so that we don't
    #               have to check the datastore to see if we need to update
    #               until the time has come.
    if not memcache.add('feed-update-lock:%s' % feed_key_name, 'locked', MAX_AGE_MIN*60):
        return True

    def txn():
        feed = Feed.get_by_key_name(feed_key_name)
        if not feed:
            return None
        if feed.needs_update():
            if not feed.updating:
                feed.updating = True
                feed.put()
                # enqueue a task to do the updating
                taskqueue.add(url='/task/update_feed', params=dict(f=feed_key_name),
                              transactional=True)
            return True
        return False
    return db.run_in_transaction(txn)
