from datetime import datetime
import wsgiref.handlers

from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp

import settings
import utils

from handler import BaseHandler
from models import Photo

class AdminIndex(BaseHandler):
    def get(self):
        if users.is_current_user_admin():
            self.render_html("admin_index", {'logout_url': users.create_logout_url("/")})
        else:
            self.redirect(users.create_login_url("/admin/"))

def get_photo_id(date_posted, slug):
    return "%s-%s" % (date_posted.strftime("%Y-%m-%d"), slug)

class PhotoAdd(BaseHandler):
    def get(self):
        self.render_html("photo_edit")

    def post(self):
        if not self.request.get('file'):
            return

        date_posted = utils.strptime_for_edit(self.request.get('date_posted'))
        file = db.Blob(self.request.get('file'))
        thumbnail = images.resize(file, 128, 128)

        photo = Photo(title=self.request.get('title'),
                      id=get_photo_id(date_posted, self.request.get('slug')),
                      location=self.request.get('location'),
                      description=self.request.get('description'),
                      date_posted=date_posted,
                      content_type="image/jpeg", # TODO
                      file=file,
                      thumbnail=thumbnail)

        photo.put()

        self.redirect(photo.get_url())

class PhotoEdit(BaseHandler):
    def get(self, id):
        photo = Photo.gql("WHERE id = :1", id).get()
        self.render_html("photo_edit", {'photo': photo})

    def post(self, id):
        photo = Photo.gql("WHERE id = :1", id).get()

        date_posted = utils.strptime_for_edit(self.request.get('date_posted'))
        photo.title = self.request.get('title')
        photo.id = get_photo_id(date_posted, self.request.get('slug'))
        photo.location = self.request.get('location')
        photo.description = self.request.get('description')
        photo.date_posted = date_posted
        if self.request.get('file'):
            photo.file = db.Blob(self.request.get('file'))
            photo.thumbnail = images.resize(photo.file, 128, 128)

        photo.put()

        self.redirect(photo.get_url())

def main():
    application = webapp.WSGIApplication(
        [(r"^/admin/$", AdminIndex),
         (r"^/admin/photo/add/$", PhotoAdd),
         (r"^/admin/photo/(?P<id>[a-z0-9-]+)/edit/$", PhotoEdit)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
