from google.appengine.ext import ndb

class Poll(ndb.Model):
	"""Models a poll scraping result"""
	updated = ndb.DateTimeProperty(auto_now=True)
	poll	= ndb.PickleProperty(compressed=True)