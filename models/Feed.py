import datetime

from google.appengine.ext import db

CATEGORIES = {
    'ccc': 'all community',
    'eee': 'all event',
    'sss': 'all for sale / wanted',
    'ggg': 'all gigs',
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

class Feed(db.Model):
    # primary key will contain URL query params which identify this feed
    last_update = db.DateTimeProperty(required=True, indexed=False, default=datetime.datetime(2000,1,1))
    updating = db.BooleanProperty(required=True, indexed=False, default=False)

    # attribute not put in datastore (stores values decomposed from key_name)
    _values = db.ListProperty(str)

    def extract_values(self):
        if self._values:
            return
        self._values = self.key().name().split('|', 10)
        self._values[8] = self._values[8].split('+')

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
            return 'At least $%s' % self.min_ask
        elif self.max_ask:
            return 'No more than $%s' % self.max_ask
        else:
            return 'Any'

    @property
    def num_bedrooms(self):
        return self._values[4]

    @property
    def allow_cats(self):
        return self._values[5]=='c'

    @property
    def allow_dogs(self):
        return self._values[6]=='d'

    def pets_str(self):
        if self.allow_cats and self.allow_dogs:
            return 'Cats and Dogs OK'
        elif self.allow_cats:
            return 'Cats only'
        elif self.allow_dogs:
            return 'Dogs only'
        else:
            return 'Any'

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

    def __repr__(self):
        return 'Feed(city=%s cat=%s $=%s-%s num_br=%s cats=%s dogs=%s neighbs=%s q_type=%s q=%s updated=%s)' % \
               (self.city, self.min_ask, self.max_ask, self.num_bedrooms, self.allow_cats, self.allow_dogs, self.neighborhoods, self.search_type, self.query, self.last_update)
