import logging

from Action import ActionHandler
from models.UserCmt import UserCmt, MIN_RATING, MAX_RATING

class Rate(ActionHandler):
    @staticmethod
    def get_action_name():
        return "rate"

    @staticmethod
    def is_rate_limited():
        return True

    def handle_action(self, uid, cid, str_rating):
        # parse the params
        try:
            rating = int(str_rating)
            if rating<MIN_RATING or rating>MAX_RATING:
                raise ValueError
        except ValueError:
            logging.warn('invalid rating: rating=%s from_uid=%s' % (str_rating, uid))
            return self.error(400)

        cmt = self.get_cmt_from_cid(cid, uid)
        if not cmt:
            return

        # update the rating
        if cmt.rating != rating:
            cmt.rating = rating
            cmt.put()
