from google.appengine.ext import db

class Feed(db.Model):
    # primary key will contain URL query params which identify this feed
    last_update = db.DateTimeProperty(required=True, indexed=False, auto_now_add=True)

    # attribute not put in datastore (stores values decomposed from key_name)
    _values = db.ListProperty(str)

    def extract_values(self):
        if self._values:
            return
        self._values = self.key.name().split('|', 6)
        self._values[-1] = self._values[-1].split('+')

    @property
    def city(self):
        self.extract_values()
        return self._values[0]

    @property
    def max_ask(self):
        self.extract_values()
        return self._values[1]

    @property
    def num_bedrooms(self):
        self.extract_values()
        return self._values[2]

    @property
    def allow_cats(self):
        self.extract_values()
        return self._values[3]=='c'

    @property
    def allow_dogs(self):
        self.extract_values()
        return self._values[4]=='d'

    @property
    def neighborhoods(self):
        self.extract_values()
        return self._values[5]

    @property
    def query(self):
        self.extract_values()
        return self._values[6]

    @staticmethod
    def make_key_name(city, query, max_ask, num_bedrooms, allow_cats, allow_dogs, neighborhoods):
        if allow_cats:
            cats = 'c'
        else:
            cats = ''
        if allow_dogs:
            dogs = 'd'
        else:
            dogs = ''
        nstrs = '+'.join(str(n) for n in neighborhoods)
        return '|'.join(str(s) for s in [city, max_ask, num_bedrooms, cats, dogs, nstrs, query])

    def __repr__(self):
        return 'Feed(city=%s max$=%s num_br=%s cats=%s dogs=%s neighbs=%s updated=%s)' % \
               (self.city, self.max_ask, self.num_bedrooms, self.allow_cats, self.allow_dogs, self.neighborhoods, self.last_update)
