import posixpath

from mako import exceptions
import mako.lookup
import mako.template

SERVER_ERROR_URI = '500.html'

class __MakoLoader(mako.lookup.TemplateLookup):
    def __init__(self, module_directory, **kwargs):
        self.package = posixpath.normpath(module_directory).replace('/', '.')
        self.__kwargs = kwargs
        self.__collection = {}

    def get_template(self, uri):
        uri = uri.strip('/')
        try:
            return self.__collection[uri]
        except KeyError:
            return self.__load(uri)

    def __load(self, uri):
        module_name = self.package + '.' + uri.replace('.','_').replace('/','.')
        self.__collection[uri] = mako.template.ModuleTemplate(module=__import__(module_name, fromlist=[self.package]), lookup=self, **self.__kwargs)
        return self.__collection[uri]

    def put_string(self, uri, text):
        self.__collection[uri] = mako.template.Template(text, lookup=self, uri=uri, **self.__kwargs)

    def put_template(self, uri, template):
        self.__collection[uri] = template

    def render(self, uri, **kwargs):
        try:
            t = self.get_template(uri)
            return t.render(**kwargs)
        except:
            # TODO: show something a bit nicer and email the admin and log the traceback
            if uri != SERVER_ERROR_URI and False:
                return self.render(SERVER_ERROR_URI)
            else:
                return exceptions.html_error_template().render()

MakoLoader = __MakoLoader('compiled_templates')
