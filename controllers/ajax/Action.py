import logging

from google.appengine.ext import webapp

from controller_functions import is_logged_in
from models.Ad import Ad
from models.UserCmt import UserCmt
from rate_limit import RateLimiter, RL_DROP, RL_HANDLE_BUT_SEND_CAPTCHA, RL_HANDLE_NORMALLY

RL = RateLimiter('act', 2.0, 5)

class ActionHandler(webapp.RequestHandler):
    """Generic base class for action handlers.  Handles verifying that the user
    is logged in and rate limiting the action.
    """
    def do_output(self, resp):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(resp)

    def get_cmt_from_cid(self, str_cid, uid):
        key_name = uid + str_cid
        cmt = UserCmt.get_by_key_name(key_name)
        if not cmt:
            ad = Ad.get_by_id(int(str_cid))
            if not ad:
                logging.warn('%s for unknown Ad cid=%s from_uid=%s' % (self.get_action_name(), str_cid, uid))
                return False
            # create a new user comment entity for this Ad
            return UserCmt(key_name=key_name, feeds=ad.feeds)
        return cmt

    def post(self, *args, **kwargs):
        """Ensures the user is logged in and rate-limits requests if
        self.is_rate_limited() is truthy.  Then calls self.handle_action() to
        execute the requested action.
        """
        # ensure the user is logged in (UI shouldn't let tags/favorites/flags be set w/o being logged in)
        sess = is_logged_in()
        if not sess:
            #return self.do_output('error-login-required')
            #TODO: TMP!!
            uid = 'fakeuid'
        else:
            uid = sess['my_id']

        # rate limit actions to guard against bots / malicious users
        if self.is_rate_limited():
            rl = RL.rate_limit(uid)
        else:
            rl = RL_HANDLE_NORMALLY  # not rate limited
        if rl == RL_DROP:
            logging.warn("RL_DROP: %s attempt by %s" % (self.get_action_name(), uid))
            self.do_output('captcha-show')
            return  # drop this request
        elif rl == RL_HANDLE_BUT_SEND_CAPTCHA:
            logging.info("RL_HANDLE_BUT_SEND_CAPTCHA: %s attempt by %s" % (self.get_action_name(), uid))
            self.do_output('captcha-show')
        else:
            # empty response means the action was processed
            self.do_output('')

        # perform the action
        self.handle_action(uid, *args, **kwargs)

    @staticmethod
    def get_action_name():
        """Override with a name which describes the action."""
        return "action"

    @staticmethod
    def is_rate_limited():
        """Returns True if this handler is rate-limited.  Defaults to True."""
        return True

    def handle_action(self):
        """Should be overridden by children to implement the appropriate action."""
        pass
