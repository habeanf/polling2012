from google.appengine.api import memcache

import webapp2,json,jinja2,os,logging
from time import gmtime, strftime

from stateprocessing import getpolls
from datejsondecoder import dumps

CACHE_KEY = 'results'
UPDATE_TIME = 'lasttime'

jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainPage(webapp2.RequestHandler):
	def get(self):
		data = memcache.get(CACHE_KEY)
		lastupdate = memcache.get(UPDATE_TIME)
		if not data:
			logging.info('Cache miss')
			pollinfo,lastupdate = getpolls()
			data = dumps(pollinfo)
			memcache.set(CACHE_KEY,data)
			memcache.set(UPDATE_TIME,lastupdate)
		else:
			logging.info('Cache hit')

		template_values = {
			'data': data,
			'lastupdate': strftime("%a, %d %b %Y %H:%M:%S +0000", lastupdate)
		}

		template = jinja_environment.get_template('d3demo.html')

		self.response.out.write(template.render(template_values))		

app = webapp2.WSGIApplication([('/',MainPage)],debug=True)