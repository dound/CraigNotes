from google.appengine.ext import webapp

from MakoLoader import MakoLoader

class DirectToTemplate(webapp.RequestHandler):
    def get(self, template_name):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(MakoLoader.render(template_name+'.html', request=self.request))
