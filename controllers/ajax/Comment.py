import logging

from google.appengine.ext import db

from Action import ActionHandler
from HTMLCleanup import clean_html
from models.UserCmt import UserCmt, MAX_NOTE_LEN

class Comment(ActionHandler):
    @staticmethod
    def get_action_name():
        return "comment"

    @staticmethod
    def is_rate_limited():
        return True

    def handle_action(self, uid, cid):
        note = self.request.get('note')
        if len(note) > MAX_NOTE_LEN:
            logging.warn('note too long: len=%d from_uid=%s' % (len(note), uid))
            return self.error(400)
        note = clean_html(note)

        cmt = self.get_cmt_from_cid(cid, uid)
        if cmt and cmt.cmt!=note:
            cmt.cmt = note
            cmt.put()
