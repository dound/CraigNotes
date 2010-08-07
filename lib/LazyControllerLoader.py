def _istring(import_name):
    """Imports an object based on a string.
    @param import_name the dotted name for the object to import.
    @return imported object
    """
    module, obj = import_name.rsplit('.', 1)
    # __import__ can't handle unicode strings in fromlist if module is a package
    if isinstance(obj, unicode):
        obj = obj.encode('utf-8')
    return getattr(__import__(module, None, None, [obj]), obj)

class _lazy(object):
    """Handles lazily importing and instantiating a class."""
    def __init__(self, path):
        """Specify the path to the class to lazily import and instantiate."""
        self.path = path
        self.name = path.split(".")[-1]
        self.cls = None

    def __call__(self):
        """Import the specified class and return a new instantiation of it."""
        if not self.cls:
            self.cls = _istring(self.path)
        return self.cls()

def url_list(mappings):
    """Creates a webapp-compatible list of URL mappings from mappings from URL
    patterns (like the default) -> string containing the path to the request
    handler object.  The values in the returned list are wrappers around the
    handler objects which only perform the import of the handler when actually
    called.
    """
    return [(m[0], _lazy(m[1])) for m in mappings]
