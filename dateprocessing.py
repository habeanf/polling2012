#coding: utf-8
from lxml import etree
import re
from itertools import compress
import pickle
import datetime
#content = open('original.html').read().decode('utf8').encode('ascii', 'replace')
#@print (content)
tree = etree.parse("original.html",etree.HTMLParser())

states = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/h3")
other = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/p")[1:]
tables = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/table[@class='wikitable']")

pairs = zip(states,other,tables)

pctre = re.compile('(\d+|\d+\.\d+)\%.(\d+|\d+\.\d+)\%')

samplere = re.compile('.*Sample size:.*(Varies|\d+).*')

def getpcts(raw):
	d = pctre.match(raw)
	return float(d.group(1)),float(d.group(2))

class DateFromTo(object):
	def __init__(self, startDate, endDate) :
		self.startDate = startDate
		self.endDate = endDate

dates = []
for state,other,tab in pairs[:46]:
	for row in tab.xpath("tr")[1:]:
		if len(row.xpath("td/a|td/br"))>2:
			dates.append(row.xpath("td[2]/text()"))
		if len(row.xpath("td/p/a|td/p/br"))>2:
			dates.append(row.xpath("td[2]/text()"))

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

def blah(x):
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

structuredDates = [ blah(ds)  for ds in dates ]
#print( dates )
for sd in structuredDates:
	print(sd.startDate, sd.endDate)

# map(lambda x: print("s"),  structuredDates )
