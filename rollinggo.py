import urllib
import webapp2
import jinja2
import os
import datetime

from google.appengine.ext import ndb

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"), autoescape=True)

# Handlers
class Main(webapp2.RequestHandler):
    # Handler for the front page.

    def get(self):
        template = jinja_environment.get_template('main.htm')
        self.response.out.write(template.render())

# Handler for the Search page
class PublicSearch(webapp2.RequestHandler):
    def get(self):
        query = ndb.gql("SELECT * "
                        "FROM Events "
                        )
        template_values = {"events" : query,}
        template = jinja_environment.get_template('publicsearch.htm')
        self.response.out.write(template.render(template_values))

class Events(ndb.Model):
    name = ndb.StringProperty()
    desc = ndb.StringProperty()

class Promote(webapp2.RequestHandler):
    def get(self):
        query = ndb.gql("SELECT * "
                        "FROM Events "
                        )
        template_values = {"events" : query,}
        template = jinja_environment.get_template('promote.htm')
        self.response.out.write(template.render(template_values))

    def post(self):
        event = Events(name = self.request.get('name'), desc = self.request.get('desc'))
        event.put()
        self.redirect('/promote')


app = webapp2.WSGIApplication([('/', Main),
                               ('/publicsearch', PublicSearch),
                               ('/promote', Promote)],
                              debug=True)
