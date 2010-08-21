import logging

from google.appengine.api import memcache

from Action import ActionHandler
from models.Feed import Feed

class IsFeedReady(ActionHandler):
    @staticmethod
    def get_action_name():
        return "isfeedready"

    @staticmethod
    def is_rate_limited():
        return True

    def handle_action(self, uid, feed_key_name):
        ret = memcache.get('feed-update-result:%s' % feed_key_name)
        if ret is None:
            self.do_output('not-ready')
        else:
            self.do_output('ready%s' % ret)
