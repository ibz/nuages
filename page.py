import wsgiref.handlers

from google.appengine.ext import webapp

from handler import BaseHandler
from models import Page

class View(BaseHandler):
    def get(self, slug):
        page = Page.gql("WHERE slug = :1", slug).get()
        self.render_html("page_view", {'page': page})

def main():
    application = webapp.WSGIApplication(
        [(r"^/(?P<slug>[a-z0-9-]+)$", View)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
