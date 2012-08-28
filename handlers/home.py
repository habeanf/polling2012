from google.appengine.api import memcache

import webapp2,json,jinja2,os,logging
from time import gmtime, strftime

from stateprocessing import getpolls
from datejsondecoder import dumps
from model.objects import Poll

try: 
    from local_settings import ga_id
except ImportError:
    ga_id = ''

jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainPage(webapp2.RequestHandler):
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

		template_values = {
			'data': dumps(pollobj.poll),
			'lastupdate': pollobj.updated,
			'ga_id': ga_id
		}

		template = jinja_environment.get_template('d3demo.html')

		self.response.out.write(template.render(template_values))		

class RefreshHandler(webapp2.RequestHandler):
	def get(self):
		logging.info("Refreshing Polls")
		getpolls()
		if 'X-AppEngine-Cron' in self.request.headers:
			logging.info("Cron Triggered")
		self.redirect("/")

app = webapp2.WSGIApplication([	('/',MainPage),
							 	('/refresh',RefreshHandler)],debug=True)