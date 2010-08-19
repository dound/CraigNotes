import logging

from Action import ActionHandler
from models.UserCmt import UserCmt

class Hide(ActionHandler):
    @staticmethod
    def get_action_name():
        return "hide/unhide"

    @staticmethod
    def is_rate_limited():
        return True

    def handle_action(self, uid, action, cid):
        hide = (action is None)
        cmt = self.get_cmt_from_cid(cid, uid)
        if not cmt:
            return

        if cmt.hidden != hide:
            cmt.hidden = hide
            cmt.put()
