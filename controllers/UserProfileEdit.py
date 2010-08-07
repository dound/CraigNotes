import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp

from MakoLoader import MakoLoader

from controller_functions import is_logged_in
from FormHandler import FormHandler, validate_string
from models.User import User

GET_PARAMS = ('dname', 'email')

class UserProfileEdit(FormHandler):
    def get(self):
        session = is_logged_in(self)
        if not session:
            return

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render('userprofile_edit.html', request=self.request,
                                                  display_name=session['my_dname'], email=session['my_email']))

    def post(self):
        session = is_logged_in(self)
        if not session:
            return

        req = self.request
        errors = {}
        dn = validate_string(req, errors, 'dname', 'display name', 100)
        email = validate_string(req, errors, 'email', 'email', 100)

        if len(errors):
            return self.redirect_to_self(errors)

        uid = session['my_id']
        user = User.get_by_key_name(uid)
        if user.display_name!=dn or user.email!=email:
            str_update = "dn=%s email=%s ==> dn=%s email=%s" % (user.display_name, user.email, dn, email)
            user.display_name = dn
            user.email = email
            try:
                user.put()
            except Exception, e:
                logging.info("Unable to update user profile: " + str_update)
                return self.redirect_to_self({'err':'Unable to update your profile.  Please try again later'})

            # profile has been updated
            session['my_dname'] = dn
            session['my_email'] = email
            logging.info("Updated user profile: " + str_update)
            memcache.delete('u+c%s' % uid) # clear saved user_info
        self.redirect('/user/%s/%s' % (uid, user.get_nice_name()))
