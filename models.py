import os
import re
from datetime import datetime
from StringIO import StringIO
from time import strptime

from google.appengine.api import mail
from google.appengine.ext import db

from lib import EXIF

import settings
import utils

class Photo(db.Expando):
    id = db.StringProperty()
    title = db.StringProperty()

    content_type = db.StringProperty()
    file = db.BlobProperty()
    thumbnail = db.BlobProperty()

    date_posted = db.DateTimeProperty()

    location = db.StringProperty()
    description = db.StringProperty()

    view_count = db.IntegerProperty()

    def get_date_posted_rfc3339(self):
        return utils.strftime_rfc3339(self.date_posted)

    def get_date_posted_for_edit(self):
        return utils.strftime_for_edit(self.date_posted)

    def get_slug(self):
        return "-".join(self.id.split("-")[3:])

    def get_url(self):
        return "/photo/%s/" % self.id

    def get_edit_url(self):
        return "/admin/photo/%s/edit/" % self.id

    def get_comments_url(self):
        return "%scomments/" % self.get_url()

    def get_file_url(self):
        return "%sfile/" % self.get_url()

    def get_thumbnail_file_url(self):
        return "%sthumbnail/" % self.get_url()

    def get_previous_by_date(self):
        query = db.Query(Photo)
        query.filter("date_posted <", self.date_posted)
        query.order("-date_posted")
        return query.get()

    def get_next_by_date(self):
        query = db.Query(Photo)
        query.filter("date_posted >", self.date_posted)
        query.order("date_posted")
        return query.get()

    def get_properties(self):
        file = StringIO(self.file)
        exif = EXIF.process_file(file)
        def get_exif_property(name):
            return exif.has_key(name) and exif[name] or None
        make = get_exif_property("Image Make")
        model = get_exif_property("Image Model")
        camera = "%s, %s" % (make, model)
        return [{'name': "Location", 'value': self.location},
                {'name': "Description", 'value': self.description},
                {'name': "Shutter speed", 'value': get_exif_property("EXIF ExposureTime")},
                {'name': "F number", 'value': get_exif_property("EXIF FNumber")},
                {'name': "Focal length", 'value': get_exif_property("EXIF FocalLength")},
                {'name': "ISO", 'value': get_exif_property("EXIF ISOSpeedRatings")},
                {'name': "Flash", 'value': get_exif_property("EXIF Flash")},
                {'name': "Camera", 'value': camera},
                {'name': "Date taken", 'value': get_exif_property("EXIF DateTimeOriginal")}]

class Comment(db.Model):
    photo  = db.ReferenceProperty(Photo)
    name   = db.StringProperty()
    email  = db.StringProperty()
    url    = db.StringProperty()
    notify = db.BooleanProperty()
    text   = db.TextProperty()
    date   = db.DateTimeProperty(auto_now_add=True)
    ip_address = db.StringProperty()

    def __cmp__(self, other):
        return cmp(self.date, other.date)

    def _send_mails(self):
        mail.send_mail(sender=settings.admin_email,
                        to=settings.admin_email,
                        subject="New comment posted",
                        body="You have a new comment!\n"
                             "Name: %(name)s\nEmail: %(email)s\nURL: %(url)s\n"
                             "Text: %(text)s" % {'name': self.name,
                                                 'email': self.email,
                                                 'url': self.url,
                                                 'text': self.text})
        query = db.Query(Comment)
        query.filter("photo =", self.photo)
        query.filter("notify =", True)
        emails_sent = []
        for comment in query:
            if comment.email and comment.email not in emails_sent:
                mail.send_mail(sender=settings.admin_email,
                               to=comment.email,
                               subject="New comment posted",
                               body="A new comment was posted by %(name)s.\n"
                                    "\"%(text)s\"" % {'name': self.name,
                                                      'text': self.text})
                emails_sent.append(comment.email)

    def put(self):
        db.Model.put(self)
        self._send_mails()

class Page(db.Model):
    title = db.StringProperty()
    slug = db.StringProperty()
    content = db.TextProperty()
    order_in_menu = db.IntegerProperty()

    def get_url(self):
        return "/%s" % self.slug

    def get_edit_url(self):
        return "/admin/page/%s/edit/" % self.slug
