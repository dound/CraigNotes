import datetime
import logging
import re

from google.appengine.api import urlfetch
from google.appengine.ext import db, webapp

from controller_functions import is_logged_in
from FormHandler import FormHandler, validate_string
from HTMLCleanup import clean_html
from MakoLoader import MakoLoader
from models.Ad import Ad
from models.UserCmt import UserCmt

GET_PARAMS = ('ad_url',)
REDIR_URL = '/?redir_to=/tracker&info=Please%20login%20to%20manually%20track%20an%20ad.'
RE_URL_CHECK = re.compile(r'http://([a-zA-Z]+.)craigslist.org/.*')
RE_ID = re.compile(r'.*/(\d+)[.]html')
RE_TITLE = re.compile(r'<h2>(.*?)</h2>')
RE_DATE = re.compile(r'Date: (.*?)<br>')
RE_DESC = re.compile(r'<div id="userbody">((.|\n)*)</div>', re.MULTILINE)

class TrackAd(FormHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('track_ad.html', request=self.request))

    def post(self):
        session = is_logged_in(self)
        if not session:
            return self.redirect(REDIR_URL)

        req = self.request
        errors = {}

        ad_url = validate_string(req, errors, 'ad_url', 'Craigslist Ad URL')
        if ad_url:
            if ad_url[:7] != 'http://':
                ad_url = 'http://' + ad_url
            m = RE_URL_CHECK.match(ad_url)
            if not m:
                errors['ad_url'] = 'This URL does not appear to be a valid craigslist.org webpage.'
            else:
                m = RE_ID.match(ad_url)
                if not m:
                    errors['ad_url'] = 'Could not extract the ID from Ad URL'
                else:
                    cid = int(m.group(1))
        if len(errors):
            return self.redirect_to_self(GET_PARAMS, errors)

        # efficiency: get Ad and UserCmt at the same time
        to_put = []
        ad_key = db.Key.from_path('Ad', cid)
        cmt_key = db.Key.from_path('UserCmt', '%s%s' % (session['my_id'], cid))
        ad, cmt = db.get([ad_key, cmt_key])

        # download the ad if we don't already have it in our db
        if not ad:
            ret = self.fetch_and_parse_page(ad_url)
            if not ret:
                errors['ad_url'] = 'Unable to download the webpage'
                return self.redirect_to_self(GET_PARAMS, errors)
            title, desc, dt = ret
            ad = Ad(key=ad_key, feeds=['manual'], title=title, desc=desc, update_dt=dt, url=ad_url)
            to_put = [ad]
        elif 'manual' not in ad.feeds:
            ad.feeds.insert(0, 'manual')
            to_put = [ad]

        # create UserCmt
        if not cmt:
            cmt = UserCmt(key=cmt_key, feeds=ad.feeds)
            to_put.append(cmt)
        elif 'manual' in cmt.feeds:
            return self.redirect('/tracker?info=You%20are%20already%20manually%20tracking%20that%20ad.')
        elif cmt.feeds != ad.feeds:
            cmt.feeds = ad.feeds
            to_put.append(cmt)

        # save the new entities
        if to_put:
            db.put(to_put)

        # redirect the user to the feed page
        self.redirect('/tracker?info=Added%20Ad%20%23' + str(cid) + '%20to%20your%20manually%20specified%20list.')

    def fetch_and_parse_page(self, url):
        try:
            resp = urlfetch.fetch(url)
        except urlfetch.Error, e:
            logging.warn('Failed to fetch Craigslist page for a specific ad (%s) due to fetch failure: %s' % (url, e))
            self.error(500)
            return False
        if resp.status_code != 200:
            logging.warn('Craigslist ad page fetch (%s) returned an unexpected status code (%s): %s' % (url, resp.status_code, resp.content))
            self.error(500)
            return False

        html = resp.content
        m = RE_TITLE.search(html)
        if not m:
            title = 'unknown'
            logging.warn('Unable to extract title from Craigslist ad page: %s' % url)
        else:
            title = clean_html(m.group(1))

        m = RE_DESC.search(html)
        if not m:
            logging.warn('Unable to extract description from Craigslist ad page: %s' % url)
            desc = 'unknown'
        else:
            desc = clean_html(m.group(1))

        m = RE_DATE.search(html)
        if not m:
            logging.warn('Unable to extract date from Craigslist ad page: %s' % url)
            dt = datetime.datetime.now()
        else:
            str_dt = m.group(1)
            try:
                dt = datetime.datetime.strptime(str_dt[:-4], '%Y-%m-%d, %I:%M%p')
            except:
                logging.warn('Unable to parse date (%s) from Craigslist ad page: %s' % (str_dt, url))
                dt = datetime.datetime.now()

        return (title, desc, dt)
