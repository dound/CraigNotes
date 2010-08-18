from time import time

from google.appengine.api import memcache
from google.appengine.ext import webapp

import captcha
from gaesessions import get_current_session

RL_HANDLE_NORMALLY = 1
RL_HANDLE_BUT_SEND_CAPTCHA = 2
RL_DROP = -1

def make_mckey(op_type, uid):
    return "rl-%s-%s" % (op_type, uid)

def note_captcha_solved(op_type, uid):
    memcache.delete(make_mckey(op_type, uid))

class RateLimiter(object):
    def __init__(self, op_type, secs_per_op, max_tokens, send_captcha_token_thresh=1):
        """Initialize a rate-limiter.
        ``op_type`` - a unique identifier of the operation being rate limited (used for part of the memcache key).
        ``secs_per_op`` - minimum time required between operations
        ``max_tokens`` - maximum number of operations which can be done beyond the base rate
        ``send_captcha_token_thresh`` - when we reach this number of tokens, a captcha will be requested.  Setting this greater than zero gives the front-end a chance to make another request(s) before answering a captcha.
        """
        self.op_type = op_type
        self.secs_per_op = float(secs_per_op)
        self.max_tokens = int(max_tokens)
        self.send_captcha_token_thresh = int(send_captcha_token_thresh)
        if self.max_tokens < 0:
            raise ValueError('max_tokens must be at least 0')
        if self.send_captcha_token_thresh < 0:
            raise ValueError('send_captcha_token_thresh must be at least 0')

    def captcha_solved(self, uid):
        note_captcha_solved(self.op_type, uid)

    def rate_limit(self, uid, captcha_solved=False):
        """Returns RL_HANDLE_NORMALLY if the request should be handled normally.
        Returns RL_HANDLE_BUT_SEND_CAPTCHA if the request should be handled AND a captcha should be issued.
        Returns RL_DROP if the request should be dropped because an outstanding captcha challenge has not been solved.

        ``uid`` - unique identifier for the current user
        ``captcha_solved`` - if True, the rate limiter will be reset for this user and operation type.
        """
        mckey = make_mckey(self.op_type, uid)
        if captcha_solved:
            state = None  # treat the request as a new one since the user is human
        else:
            state = memcache.get(mckey)

        if not state:
            prev_time, tokens_left = 0, self.max_tokens
        else:
            prev_time, tokens_left = state

        ret = RL_HANDLE_NORMALLY
        now = time()
        if prev_time + self.secs_per_op > now:
            # request was made more quickly than we allow: deduct a token
            tokens_left -= 1
            if tokens_left < 0:
                ret = RL_DROP
            elif tokens_left <= self.send_captcha_token_thresh:
                ret = RL_HANDLE_BUT_SEND_CAPTCHA
        else:
            extra_time = now - prev_time - self.secs_per_op
            tokens_regained = int(extra_time / self.secs_per_op)
            tokens_left = min(self.max_tokens, tokens_left+tokens_regained)

        if ret != RL_DROP:
            timeout = (self.max_tokens+1) * self.secs_per_op
            memcache.set(mckey, (now, tokens_left), timeout)
        return ret

class CaptchaHandler(webapp.RequestHandler):
    def do_output(self, resp=''):
        cb = self.request.get('callback')
        if cb:
            self.response.headers['Content-Type'] = 'text/javascript'
            cbid = self.request.get('cbid')
            self.response.out.write('%s({"cbid":"%s", "resp":"%s"});' % (cb, cbid, resp))
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(resp)

    def get(self, op_type):
        return self.post(op_type)

    def post(self, op_type):
        self.response.headers['Content-Type'] = 'text/plain'
        session = get_current_session()
        if not session.is_active() or not session.has_key('my_id'):
            return self.do_output('captcha-not-logged-in')
        uid = session['my_id']

        challenge = self.request.get('recaptcha_challenge_field')
        response = self.request.get('recaptcha_response_field')
        if not challenge or not response:
            return self.do_output('captcha-bad-response')

        resp = captcha.submit(challenge, response, '6LdFE7oSAAAAAPuHb_bHlp4i6omCQkPlWySQjShD', self.request.remote_addr)
        if resp.is_valid:
            note_captcha_solved(op_type, uid)
            return self.do_output('captcha-ok')
        else:
            return self.do_output('captcha-failed-%s' % resp.error_code)
