from datetime import datetime, timedelta
import logging
import re

from google.appengine.api import memcache, urlfetch
from google.appengine.ext import db, webapp

import feedparser
from HTMLCleanup import clean_html
from MakoLoader import MakoLoader
from models.Ad import Ad
from models.Feed import Feed

RE_CID = re.compile(r'.*/(\d+)[.]html')

def onlyascii(char):
    if ord(char) < 0 or ord(char) > 127:
        return ''
    else:
        return char

class UpdateFeed(webapp.RequestHandler):
    def post(self):
        feed_key_name = self.request.get('f')
        feed = Feed.get_by_key_name(feed_key_name)
        if not feed:
            return
        feed.extract_values()
        feed_url = feed.make_url(rss=True)
        fhid = feed.hashed_id

        # get the feed from Craigslist
        try:
            resp = urlfetch.fetch(feed_url)
        except urlfetch.Error, e:
            logging.warn('Failed to fetch Craigslist feed (%s) due to fetch failure: %s' % (feed_url, e))
            return self.error(500)
        if resp.status_code != 200:
            logging.warn('Craigslist feed fetch (%s) returned an unexpected status code (%s): %s' % (feed_url, resp.status_code, resp.content))
            return self.error(500)

        # parse the feed
        ads = []
        now = datetime.now()
        try:
            rss = feedparser.parse(resp.content)
        except Exception,e:
            logging.error('unable to parse RSS feed from %s: %s' % (feed_url, resp.content))
            return

        for e in rss['entries']:
            link = e['link']
            m_cid = RE_CID.match(link)
            if not m_cid:
                logging.error('unable to extract CID from link: %s' % link)
                continue
            cid = int(m_cid.groups()[0])
            ad_key = db.Key.from_path('Ad', cid)
            title = filter(onlyascii, clean_html(e['title'], [], []))  # not tags allowed
            desc = filter(onlyascii, clean_html(e['summary']))         # default tags allowed
            updated_str = e['updated']
            try:
                offset = int(updated_str[-5:][:2])
            except:
                logging.error('unable to extract UTC offset for link=%s: %s' % (link, updated_str))
                offset = 0
            try:
                dt = datetime.strptime(updated_str[:len(updated_str)-6], '%Y-%m-%dT%H:%M:%S')
                updated = dt + timedelta(hours=offset/100)
            except ValueError:
                logging.error('unable to parse the datetime for link=%s: %s' % (link, updated_str))
                updated = now
            if not title:
                logging.warn('Got Ad (%s) with no title from RSS feed' % link)
            elif not desc:
                logging.warn('Got Ad (%s) with no desc from RSS feed' % link)
            else:
                ad = Ad(key=ad_key, feeds=[fhid], title=title, desc=desc, update_dt=updated, url=link)
                ads.append(ad)

        # determine which ads already exist in the datastore
        ads_to_put = []
        keys = [ad.key() for ad in ads]
        existing_ads = db.get(keys)
        for i in xrange(len(keys)):
            ad = ads[i]
            e_ad = existing_ads[i]
            if e_ad is None:
                ads_to_put.append(ad)
            elif ad.feeds[0] not in e_ad.feeds:
                # If the ad is not listed as being in feeds we already know it
                # to be in, then ad the existing feed list to the new ad.  Do
                # it this way so that we store the latest ad info just retrieved.
                ad.feeds += e_ad.feeds
                ads_to_put.append(ad)

                # EFFICIENCY: Technically, we need to update all UserCmt objects
                # which have a denormalized copy of this value too.  However,
                # this would be mostly worthless since this new feed is probably
                # only used a single/few users - better to just do it on-demand.
                # (search view does this on-demand updating)
            elif ad.update_dt != e_ad.update_dt:
                # If the ad was updated but the feed is already present in the
                # existing ad entity's feeds
                ad.feeds = e_ad.feeds
                ads_to_put.append(ad)
            # else: the add hasn't changed => no need to send it to the datastore

        # create/update Ad entities
        if ads_to_put:
            db.put(ads_to_put)

        # update memcache entries which specify when a feed was last updated and the number of updated ads
        mc_dict = {'feed-update-dt:%s'     % feed_key_name : now,
                   'feed-update-result:%s' % feed_key_name : len(ads_to_put)
                  }
        memcache.set_multi(mc_dict)

        # update the Feed entity too
        feed.last_update = now
        feed.updating = False
        feed.put()

        logging.info('FEED UPDATED: %d new/updated ads for %s' % (len(ads_to_put), feed_url))
