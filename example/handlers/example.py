import webapp2
from handlers.base import BaseHandler
from helpers import is_debug

class ExampleHandler(BaseHandler):
    def get(self):
        self.render_response('example.html')

routes = [
    webapp2.Route('/', handler=ExampleHandler, name='example'),
]

app = webapp2.WSGIApplication(routes, config={}, debug=is_debug())
