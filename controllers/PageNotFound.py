from google.appengine.ext import webapp

from MakoLoader import MakoLoader

class PageNotFound(webapp.RequestHandler):
    def get(self):
        return PageNotFound.render(self)

    @staticmethod
    def render(handler):
        handler.error(404)
        handler.response.out.write(MakoLoader.render('404.html', request=handler.request))
        # TODO: make a better 404 page, notify the admin
