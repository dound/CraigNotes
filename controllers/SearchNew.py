from cgi import parse_qs
import logging
import re
from urllib import urlencode

from google.appengine.api import memcache
from google.appengine.ext import webapp

from controller_functions import is_logged_in
from FormHandler import FormHandler, validate_int, validate_string
from MakoLoader import MakoLoader
from models.Feed import Feed, CATEGORIES
from models.User import User

GET_PARAMS = ('rss_url', 'city', 'category', 'query', 'title_only', 'min_cost', 'max_cost', 'num_bedrooms', 'cats', 'dogs')
REDIR_URL = '/?redir_to=/new&info=Please%20login%20to%20start%20tracking%20a%20new%search.'
RE_RSS_URL = re.compile(r'http://([^.]+).craigslist.org/(search/)?(...)/?[^?]*([?](.*))?')

def parse_rss_url(url):
    """Parses a RSS URL from Craigslist and returns the Feed key which describes it."""
    m = RE_RSS_URL.match(url)
    if not m:
        return None
    groups = m.groups()
    city, cat, qparams = groups[0], groups[2], groups[4]
    cat2, min_ask, max_ask, nb, c, d, hp, n, st, q = parse_rss_url_params(qparams)
    if cat2:
        cat = cat2
    #return Feed.make_key_name(city, cat, min_ask, max_ask, nb, c, d, hp, n, st, q)
    return (city, cat, min_ask, max_ask, nb, c, d, hp, n, st, q)

def parse_rss_url_params(qparams):
    if not qparams:
        return ('', '', '', '', '', '', '', [], '', '')
    params = parse_qs(qparams)
    return (params.get('catAbb',[''])[0],    params.get('minAsk',[''])[0],
            params.get('maxAsk',[''])[0],    params.get('bedrooms',[''])[0],
            params.get('addTwo',[''])[0],    params.get('addThree',[''])[0],
            params.get('hasPic',[''])[0],    params.get('nh', []),
            params.get('srchType',['A'])[0], params.get('query', [''])[0])

class SearchNew(FormHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('search_new.html', request=self.request))

    def post(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)

        req = self.request
        errors = {}
        rss_url = req.get('rss_url')
        if rss_url:
            feed_key = parse_rss_url(rss_url)
            if not feed_key:
                return self.redirect_to_errors(GET_PARAMS, {'error_rss_url':'''This URL isn't in the expected form.  Please <a href="/contact">send it to us</a> if you think this is a bug.'''})
        else:
            city = validate_string(req, errors, 'city', 'city/region', max_len=50)
            category = validate_string(req, errors, 'category', 'category', 3, CATEGORIES.keys())
            query = validate_string(req, errors, 'query', 'search string', 100, required=False)
            title_only = req.get('title_only')=='checked'
            if title_only:
                stype = 'T'
            else:
                stype = 'A'
            min_cost = validate_int(req, errors, 'min_cost', 'Minimum Cost', 0, None, False)
            max_cost = validate_int(req, errors, 'max_cost', 'Maximum Cost', 0, None, False)
            num_bedrooms = validate_int(req, errors, 'num_bedrooms', 'Number of bedrooms', 1, 8, False)
            cats = req.get('cats')=='checked'
            dogs = req.get('dogs')=='checked'
            pics = req.get('pics')=='checked'
            if len(errors):
                return self.redirect_to_self(GET_PARAMS, errors)
            feed_key = Feed.make_key_name(city, category, min_cost, max_cost,
                                          num_bedrooms, cats, dogs, pics, [], stype, query)

        # make sure the feed is in the datastore
        try:
            Feed.get_or_insert(key_name=feed_key)
        except Exception, e:
            logging.error('Unable to create new Feed (%s): %s' % (feed_key, e))
            return self.redirect_to_self(GET_PARAMS, {'err':'The service is temporarily unavailable - please try again later.'})

        # redirect the user to the feed page
        self.redirect('/view/%s' % urlencode(feed_key))
