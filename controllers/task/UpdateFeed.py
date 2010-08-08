import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import db, webapp

import feedparser
from MakoLoader import MakoLoader
from models.Feed import Feed

class UpdateFeed(webapp.RequestHandler):
    def get(self):
        feed_key_name = self.request.get('f')
        feed = Feed.get_by_key_name(feed_key_name)
        if not feed:
            return
        feed_url = feed.make_url(rss=True)

        # get the feed from Craigslist
        try:
            resp = urlfetch.fetch(feed_url)
        except urlfetch.Error, e:
            logging.warn('Failed to fetch Craigslist feed (%s) due to fetch failure: %s' % (feed_url, e))
            return self.error(500)
        if resp.status_code < 200 or resp.status_code >= 300:
            logging.warn('Craigslist feed fetch (%s) returned an unexpected status code (%s): %s' % (feed_url, resp.status_code, resp.content))
            return self.error(500)

        # parse the feed
        rss = feedparser.parse(resp.content)

        # TODO: create Ad entities from the rss dictionary!

        # update memcache key which specifies when a feed was last updated
        mc_key = 'feed-update-dt:%s' % feed_key_name
        now = datetime.datetime.now()
        dt = memcache.set(mc_key, now)

        # update the Feed entity too
        feed.last_update = now
        feed.updating = False
        feed.put()
