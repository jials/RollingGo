import urllib
import webapp2
import jinja2
import os
import datetime

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))

# This part for the front page
class MainPage(webapp2.RequestHandler):
    # Handler for the front page.

    def get(self):
        template = jinja_environment.get_template('front.html')
        self.response.out.write(template.render())


class MainPageUser(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('frontuser.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

# Datastore definitions
class Items(ndb.Model):
    # Models an item with event_name, event_link, description, and date. Key is item_id.
    item_id = ndb.IntegerProperty()
    event_name = ndb.StringProperty()
    event_link = ndb.StringProperty()
    event_type = ndb.StringProperty()
    description = ndb.TextProperty()
    rsvp = ndb.IntegerProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

class Persons(ndb.Model):
    # Models a person. Key is the email.
    next_item = ndb.IntegerProperty()  # item_id for the next item

# CurrentPerson is used for many-to-many relationship between Persons and Items
class CurrentPerson(ndb.Model):
    name = ndb.StringProperty()
    event_name = ndb.StringProperty()
    event_link = ndb.StringProperty()
    event_type = ndb.StringProperty()
    description = ndb.TextProperty()
    rsvp = ndb.StringProperty()
    date = ndb.StringProperty()


class WishList(webapp2.RequestHandler):
    """ Form for getting and displaying wishlist items. """

    def show(self):
        # Displays the page. Used by both get and post
        user = users.get_current_user()
        if user:  # signed in already

            # Retrieve person
            parent_key = ndb.Key('Persons', users.get_current_user().email())

            # Retrieve items
            query = ndb.gql("SELECT * "
                            "FROM Items "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY date DESC",
                            parent_key)

            person = CurrentPerson.query(CurrentPerson.name == users.get_current_user().email())

            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'items': query,
                'person': person,
            }

            template = jinja_environment.get_template('wishlist.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

    def get(self):
        self.show()

    def post(self):
        # Retrieve person
        parent = ndb.Key('Persons', users.get_current_user().email())
        person = parent.get()
        if person == None:
            person = Persons(id=users.get_current_user().email())
            person.next_item = 1

        item = Items(parent=parent, id=str(person.next_item))
        item.item_id = person.next_item

        item.event_name = self.request.get('event_name')
        item.event_link = self.request.get('event_link')
        item.description = self.request.get('desc')
        item.event_type = self.request.get('eventtype')
        item.rsvp = 0

        person.next_item += 1
        person.put()
        item.put()
        self.show()

class UnGo(webapp2.RequestHandler):
    def post(self):
        person = ndb.Key(urlsafe = self.request.get('itemkey'))
        person.delete()
        eventKey = Items.query(Items.event_name == self.request.get('itemname'))
        event = eventKey.get()
        event.rsvp -= 1
        event.put()
        self.redirect('/wishlist')

# For deleting an item from wish list
class DeleteItem(webapp2.RequestHandler):
    # Delete item specified by user
    def post(self):
        item = ndb.Key('Persons', users.get_current_user().email(), 'Items', self.request.get('itemid'))
        item.delete()
        self.redirect('/wishlist')

class RSVPItem(webapp2.RequestHandler):
    # increment RSVP count when GO button is clicked
    def post(self):
        itemname = self.request.get('itemname')
        
        person = CurrentPerson(name = users.get_current_user().email(),
                            event_name = self.request.get('itemname'),
                            event_link = self.request.get('itemlink'),
                            event_type = self.request.get('itemtype'),
                            description = self.request.get('itemdesc'),
                            rsvp = self.request.get('itemrsvp'),
                            date = self.request.get('itemdate'))
        person.put()
        
        query = ndb.gql("SELECT *"
                        "FROM Items")
        for item in query:
            if item.event_name == itemname:
                item.rsvp += 1
                item.put()
        template_values = {'event_name': itemname,}
        template = jinja_environment.get_template('rsvp.html')
        self.response.out.write(template.render(template_values))

# Handler for the Search page
class Search(webapp2.RequestHandler):
    # Display search page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            # Retrieve items
            query = ndb.gql("SELECT * "
                            "FROM Items ")

            template_values = {
                'user_mail': users.get_current_user().email(),
                'logout': users.create_logout_url(self.request.host_url),
                'items': query,
            }
            template = jinja_environment.get_template('search.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)


# Handler for returning search result
class Display(webapp2.RequestHandler):
    # Displays search result
    def post(self):
        target = self.request.get('search').rstrip()

        query = ndb.gql("SELECT * "
                        "FROM Items ")

        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'items': query,
            'search': target,
        }
        template = jinja_environment.get_template('display.html')
        self.response.out.write(template.render(template_values))

class Displaytag(webapp2.RequestHandler):
    # Displays search result

    def post(self):
        tags = self.request.get('eventtype')

        query = ndb.gql("SELECT * "
                        "FROM Items ")

        template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'items': query,
            'type': tags,
        }
        template = jinja_environment.get_template('displaytag.html')
        self.response.out.write(template.render(template_values))

# Simply redirect to front page 
class HandleOpenId(webapp2.RequestHandler):
    def get(self):
        self.redirect(self.request.host_url)

class GetOpenId(webapp2.RequestHandler):
    def get(self):
        self.redirect(users.create_login_url('/giftbook', None, federated_identity='https://openid.nus.edu.sg/'))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/giftbook', MainPageUser),
                               ('/wishlist', WishList),
                               ('/deleteitem', DeleteItem),
                               ('/search', Search),
                               ('/rsvp', RSVPItem),
                               ('/display', Display),
                               ('/displaytag', Displaytag),
                               ('/ungo', UnGo),
                               ('/getOpenId', GetOpenId),
                               ('/_ah/login_required', HandleOpenId)],
                              debug=True)

