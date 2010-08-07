from urllib import urlencode

from google.appengine.ext import webapp

class FormHandler(webapp.RequestHandler):
    def redirect_to_self(self, GET_params, errors=None):
        """Redirects back to the URL we're currently on (but will trigger a GET
        request) with any errors and all query parameters passed in the query string."""
        d = {}
        if errors:
            for k,v in errors.iteritems():
                if k != 'err':
                    d['error_' + k] = v
                else:
                    d['err'] = v
        for p in GET_params:
            d[p] = self.request.get(p)
        self.redirect(self.request.path + '?' + urlencode(d))

class QuietDict(dict):
    def get(self, key, default=''):
        """Just like dict.get, but return '' if the key isn't found."""
        return dict.get(self, key, default)

def validate_string(req, errors, param_name, desc, max_len, required=True):
    """Gets the specified query parameter and makes sure it exists and isn't too
    long and then returns it after HTML escaping it.  errors is updated and None
    is returned if an error occurs.
    """
    v = req.get(param_name)
    if not v:
        if not required:
            return None
        errors[param_name] = 'You must specify a %s.' % desc
    elif len(v) > max_len:
        errors[param_name] = '%s is too long (only %d characters allowed)' % (desc, max_len)
    return v
