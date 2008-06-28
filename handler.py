import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import settings

class BaseHandler(webapp.RequestHandler):
    def render(self, content_type, content):
        self.response.headers["Content-Type"] = content_type
        self.response.out.write(content)

    def render_template(self, content_type, template_file, data=None):
        if data is None:
            data = {}
        data['admin'] = users.is_current_user_admin()
        data['settings'] = settings

        template_path = os.path.join(os.path.dirname(__file__), "templates")
        output = template.render(os.path.join(template_path, template_file), data)

        self.render(content_type, output)

    def render_html(self, template_name, data=None):
        self.render_template("text/html", "%s.html" % template_name, data)

    def render_atom(self, template_name, data=None):
        self.render_template("application/atom+xml", "%s.xml" % template_name, data)
