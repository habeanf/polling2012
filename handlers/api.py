from google.appengine.api import memcache
import webapp2,logging

from stateprocessing import getpolls
from datejsondecoder import dumps
from model.objects import Poll

class ApiPage(webapp2.RequestHandler):
	def get(self):
		pollobj = Poll.get_by_id('us_state_2012')
		if not pollobj:
			logging.info('Poll does not exist')
			getpolls()
			pollobj = Poll.get_by_id('us_state_2012')
			if pollobj is None:
				raise Exception("Poll not found")
		else:
			logging.info('Poll found')

		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(dumps(pollobj.poll))

app = webapp2.WSGIApplication([('/api',ApiPage)],debug=True)
