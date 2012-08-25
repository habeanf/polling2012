from google.appengine.api import memcache
import webapp2,json

from stateprocessing import getpolls
from datejsondecoder import dumps

CACHE_KEY = 'results'

class MainPage(webapp2.RequestHandler):
	def get(self):
		data = memcache.get(CACHE_KEY)
		if not data:
			pollinfo = getpolls()
			data = dumps(pollinfo)
			memcache.set(CACHE_KEY,data)
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(data)

app = webapp2.WSGIApplication([('/',MainPage)],debug=True)