#coding: utf-8
import re
import datetime

class DateFromTo(object):
	def __init__(self, startDate, endDate) :
		self.startDate = startDate
		self.endDate = endDate
	def __str__(self):
		return '('+str(self.startDate)+','+str(self.endDate)+')'

regexStr = """
^
(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)
(?P<startdate>[0-9]{1,2})
.+?
(?P<secondmonth>January|February|March|April|May|June|July|August|September|October|November|December)?
.*?
(?P<lastdate>[0-9]{1,2})?
,?
(?P<year>20[0-9]{2})$
"""

regex = re.compile( regexStr.replace('\n','') )

monthsText = ["January","February","March","April","May","June","July","August","September","October","November","December"]
#print( regex.search( dates[0][0].replace(' ','') ).groups()[0] )
def cleanStr(astr):
	return astr.replace(' ','').encode('utf8').replace('–','-').encode('ascii')

def getDateSpan(x):
	s = cleanStr(x[0])
	try:
		regxRes = regex.search( s )
		startMonth = monthsText.index( regxRes.group( 'month' ) ) +1
		startDate = int(regxRes.group( 'startdate' ))
		secondMonth = monthsText.index( regxRes.group( 'secondmonth' ) ) +1 if regxRes.group( 'secondmonth' ) else startMonth
		lastDate = int(regxRes.group( 'lastdate' ) if regxRes.group( 'lastdate' ) else startDate)
		year = int(regxRes.group( 'year' ))
		return DateFromTo( datetime.date(year, startMonth, startDate) , datetime.date(year, secondMonth, lastDate) )
	except Exception, err:
		print err
		print( "string:" + s )