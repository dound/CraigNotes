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

def validate_string(req, errors, param_name, desc, max_len=None, allowed_values=None, required=True):
    """Gets the specified query parameter and makes sure it exists and isn't too
    long and then returns it after HTML escaping it.  errors is updated and None
    is returned if an error occurs.
    """
    v = req.get(param_name)
    if not v:
        if not required:
            return None
        errors[param_name] = 'You must specify a %s.' % desc
    elif max_len and len(v) > max_len:
        errors[param_name] = '%s is too long (only %d characters allowed).' % (desc, max_len)
    elif allowed_values and v not in allowed_values:
        errors[param_name] = 'Please choose a valid value for %s.' % desc
    return v

def validate_int(req, errors, param_name, desc, min_value=None, max_value=None, required=True):
    v = req.get(param_name)
    if not v:
        if not required:
            return None
        errors[param_name] = 'You must specify a %s.' % desc
        return
    try:
        v = int(v)
    except ValueError:
        errors[param_name] = '%s must be a whole number.' % desc
        return
    if min_value and min_value > v:
        errors[param_name] = '%s must be greater than or equal to %s.' % (desc, min_value)
        return None
    if max_value and max_value < v:
        errors[param_name] = '%s must be less than or equal to %s.' % (desc, max_value)
        return None
    return v
