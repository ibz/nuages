import wsgiref.handlers

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp

import settings

from handler import BaseHandler
from models import Comment
from models import Photo
from models import PhotoCategory
from models import PhotoLocation

def update_view_count(photo):
    if not photo:
        return
    if not users.is_current_user_admin():
        if not photo.view_count:
            photo.view_count = 1
        else:
            photo.view_count += 1
        photo.put()

class Index(BaseHandler):
    def get(self):
        photo = db.Query(Photo).order('-date_posted').get()
        update_view_count(photo)
        self.render_html("photo_view", {'photo': photo})

class PhotoBrowse(BaseHandler):
    NUM_PER_PAGE = 15

    def _get_paginator(self, page, page_count):
        return {'page_number': page,
                'previous_page_number': page - 1,
                'next_page_number': page + 1,
                'has_previous_page': page - 1 >= 1,
                'has_next_page': page + 1 <= page_count,
                'num_pages': page_count}

    def get(self):
        page = self.request.get('page')
        location_filter = self.request.get('location')
        category_filter = self.request.get('category')

        query = db.Query(Photo)
        if location_filter:
            location = db.Query(PhotoLocation).filter("id = ", location_filter).get()
            if location:
                query.filter("location_ref = ", location)
            else:
                location_filter = None
        if category_filter:
            category = db.Query(PhotoCategory).filter("id = ", category_filter).get()
            if category:
                query.filter("categories_ref = ", category)
            else:
                category_filter = None
  
        query.order("-date_posted")

        count = query.count()
        page_count = (count / self.NUM_PER_PAGE) + (count % self.NUM_PER_PAGE and 1)

        if page == "last":
            page = page_count
        elif not page:
            page = 1
        else:
            page = int(page)

        photos = query.fetch(self.NUM_PER_PAGE, (page - 1) * self.NUM_PER_PAGE)

        if not location_filter and not category_filter:
            title = "Browse archive"
            filter = ""
        elif location_filter:
            title = "Browse photos from %s" % location.name
            filter = "&location=%s" % location_filter
        elif category_filter:
            title = "Browse photos from category %s" % category.name
            filter = "&category=%s" % category_filter

        self.render_html("photo_browse",
                         {'photos': photos,
                          'paginator': self._get_paginator(page, page_count),
                          'filter': filter,
                          'title': title})

class PhotoCategories(BaseHandler):
    def get(self):
        categories = [c for c in db.Query(PhotoCategory).order("name")]
        categories = [(c, db.Query(Photo).filter("categories_ref = ", c.key()).count(1000)) for c in categories]
        categories = [c for c in categories if c[1]]
        self.render_html("photo_categories", {'categories': categories})

class PhotoLocations(BaseHandler):
    def get(self):
        locations = [(l, l.photo_set.count(1000)) for l in db.Query(PhotoLocation).order("name")]
        locations = [l for l in locations if l[1]]
        self.render_html("photo_locations", {'locations': locations})

class PhotoFeed(BaseHandler):
    def get(self):
        query = db.Query(Photo)
        query.order("-date_posted")
        photos = query.fetch(settings.num_items_in_feed)

        self.render_atom("photo_feed", {'photos': photos})

class PhotoView(BaseHandler):
    def get(self, id):
        photo = Photo.gql("WHERE id = :1", id).get()
        update_view_count(photo)
        self.render_html("photo_view", {'photo': photo})

class PhotoViewFile(BaseHandler):
    def get(self, id):
        photo = Photo.gql("WHERE id = :1", id).get()
        self.render(str(photo.content_type), photo.file)

class PhotoViewThumbnail(BaseHandler):
    def get(self, id):
        photo = Photo.gql("WHERE id = :1", id).get()
        # TODO content type
        self.render(str(photo.content_type), photo.thumbnail)

class PhotoComments(BaseHandler):
    def get(self, id):
        photo = Photo.gql("WHERE id = :1", id).get()
        comments = sorted(photo.comment_set)
        self.render_html("photo_comments", {'photo': photo,
                                            'comments': comments})

    def post(self, id):
        photo = Photo.gql("WHERE id = :1", id).get()

        spam = self.request.get('spam')
        if spam.upper() != "NO":
            return
        name = self.request.get('name')
        email = self.request.get('email')
        url = self.request.get('url')
        notify = self.request.get('notify').upper() == "ON"
        text = self.request.get('text')
        if not text:
            return

        comment = Comment(photo=photo,
                          name=name,
                          email=email,
                          url=url,
                          notify=notify,
                          text=text)
        comment.put()

def main():
    application = webapp.WSGIApplication(
        [(r"^/$", Index),
         (r"^/photo/browse/$", PhotoBrowse),
         (r"^/photo/categories/$", PhotoCategories),
         (r"^/photo/locations/$", PhotoLocations),
         (r"^/photo/feed/$", PhotoFeed),
         (r"^/photo/(?P<id>[a-z0-9-]+)/$", PhotoView),
         (r"^/photo/(?P<id>[a-z0-9-]+)/file/$", PhotoViewFile),
         (r"^/photo/(?P<id>[a-z0-9-]+)/thumbnail/$", PhotoViewThumbnail),
         (r"^/photo/(?P<id>[a-z0-9-]+)/comments/$", PhotoComments)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
