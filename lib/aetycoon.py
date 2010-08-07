"""trimmed down version of aetycoon"""

from google.appengine.ext import db

def DerivedProperty(func=None, *args, **kwargs):
    """Implements a 'derived' datastore property."""
    if func:
        # Regular invocation, or used as a decorator without arguments
        return _DerivedProperty(func, *args, **kwargs)
    else:
        # We're being called as a decorator with arguments
        def decorate(decorated_func):
            return _DerivedProperty(decorated_func, *args, **kwargs)
        return decorate

class _DerivedProperty(db.Property):
    def __init__(self, derive_func, *args, **kwargs):
        super(_DerivedProperty, self).__init__(*args, **kwargs)
        self.derive_func = derive_func

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        return self.derive_func(model_instance)

    def __set__(self, model_instance, value):
        raise db.DerivedPropertyError("Cannot assign to a DerivedProperty")

class KeyProperty(db.Property):
  """A property that stores a key, without automatically dereferencing it."""
  def validate(self, value):
    """Validate the value."""
    if isinstance(value, basestring):
        value = db.Key(value)
    if value is not None:
        if not isinstance(value, db.Key):
            raise TypeError("Property %s must be an instance of db.Key" % (self.name,))
    return super(KeyProperty, self).validate(value)
