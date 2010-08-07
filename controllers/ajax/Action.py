import logging

from google.appengine.ext import webapp

from controller_functions import is_logged_in
from models.Photo import get_photo_by_smid, Photo
from rate_limit import RateLimiter, RL_DROP, RL_HANDLE_BUT_SEND_CAPTCHA, RL_HANDLE_NORMALLY

RL = RateLimiter('act', 2.0, 3)

class ActionHandler(webapp.RequestHandler):
    """Generic base class for action handlers.  Handles verifying that the user
    is logged in and rate limiting the action.
    """
    def do_output(self, resp):
        cb = self.request.get('callback')
        if cb:
            self.response.headers['Content-Type'] = 'text/javascript'
            cbid = self.request.get('cbid')
            self.response.out.write('%s({"cbid":"%s", "resp":"%s"});' % (cb, cbid, resp))
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(resp)

    def get_photo_from_pid_or_smid(self, str_pid, str_smid, uid):
        if str_pid:
            try:
                pid = int(str_pid)
            except ValueError:
                logging.warn('invalid pid format: pid=%s from_uid=%s' % (str_pid, uid))
                self.error(400)
                return False
            photo = Photo.get_by_id(pid)
        else:
            try:
                smid = int(str_smid)
            except ValueError:
                logging.warn('invalid smid format: smid=%s from_uid=%s' % (str_smid, uid))
                self.error(400)
                return False
            photo = get_photo_by_smid(smid)

        if not photo:
            logging.warn('%s for unknown photo pid=%s smid=%s from_uid=%s' % (self.get_action_name(), str_pid, str_smid, uid))
            # not a "bad request", so just return as normal
            return False
        return photo

    def get(self):
        return self.post()

    def post(self):
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
        self.handle_action(uid)

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
