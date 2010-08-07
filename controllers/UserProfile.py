from google.appengine.api import memcache
from google.appengine.ext import webapp

from MakoLoader import MakoLoader

from controllers.PageNotFound import PageNotFound
from models.CumlContrib import get_counts
from models.User import User
from view_functions import format_date

class UserProfile(webapp.RequestHandler):
    def get(self, oid, ignore, display_name):
        mckey = "u+c:%s" % oid
        user_info = memcache.get(mckey)
        if user_info:
            dn, email, date_reg, counts = user_info
        else:
            user = User.get_by_key_name(oid)
            if not user:
                return PageNotFound.render(self)

            # SEO: force the display name in the URL to be correct
            correct_display_name = user.get_nice_name()
            if correct_display_name != display_name:
                return self.redirect('/user/%s/%s' % (oid, correct_display_name), permanent=True)

            dn, email, date_reg = user.display_name, user.email, format_date(user.date_registered)
            counts = get_counts(user_id=oid)
            user_info = (dn, email, date_reg, counts)
            memcache.set(mckey, user_info, 30)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('userprofile.html', request=self.request, display_name=dn, email=email, date_reg=date_reg, counts=counts, uid=oid))
