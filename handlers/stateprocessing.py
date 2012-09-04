#!/usr/bin/python
#coding: utf-8

import re,urllib2,logging
from lxml import etree
from itertools import compress
from pprint import pprint
from StringIO import StringIO

from dateprocessing import getDateSpan,DateFromTo
from model.objects import Poll

url = 'http://en.wikipedia.org/wiki/Statewide_opinion_polling_for_the_United_States_presidential_election,_2012'

pctre = re.compile('(\d+|\d+\.\d+)\%.(\d+|\d+\.\d+)\%')

samplere = re.compile('.*Sample size: ?(?P<size>Varies|\d+|n\/a)-?\d* ?(?P<votertype>LV|RV)? ?.*')

marginre = re.compile('.*Margin of error(: .| .* )(?P<margin>\d+|\d+.\d+)%.*')

def getpcts(raw):
	d = pctre.match(raw)
	return float(d.group(1)),float(d.group(2))


def getpollresults(row,isfirst):
	democrat = None
	demopct = None
	republic = None
	repubpct = None
	leadmargin = None
	indexshift = 2 if isfirst else 0
	democrat = row.xpath("td[%d]/text()|td[%d]/a/text()|td[%d]/a/b/text()|td[%d]/b/a/text()|td[%d]/b/text()" % (1+indexshift,1+indexshift,1+indexshift,1+indexshift,1+indexshift))[0]
	demopct = row.xpath("td[%d]/text()|td[%d]/a/text()|td[%d]/a/b/text()|td[%d]/b/a/text()|td[%d]/b/text()" % (2+indexshift,2+indexshift,2+indexshift,2+indexshift,2+indexshift))[0]
	republican = row.xpath("td[%d]/text()|td[%d]/a/text()|td[%d]/a/b/text()|td[%d]/b/a/text()|td[%d]/b/text()" % (3+indexshift,3+indexshift,3+indexshift,3+indexshift,3+indexshift))[0]
	repubpct = row.xpath("td[%d]/text()|td[%d]/a/text()|td[%d]/a/b/text()|td[%d]/b/a/text()|td[%d]/b/text()" % (4+indexshift,4+indexshift,4+indexshift,4+indexshift,4+indexshift))[0]
	leadmargin = float(repubpct[:-1])-float(demopct[:-1])
	return {'democrat':democrat,'democrat_pct':float(demopct[:-1]),'republican':republican,'republican_pct':float(repubpct[:-1]),'lead_margin':float(leadmargin) if abs(leadmargin)>0 else 0.0}


def getpolls():
	logging.info('Getting poll info')
	req = urllib2.Request(url, headers={'User-Agent' : "habeanf's single page scraper (please don't cut me off)"})

	tree = etree.parse(StringIO(urllib2.urlopen(req).read()),etree.HTMLParser())

	logging.info('Page retrieved')
	states = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/h3")
	other = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/p")[1:]
	tables = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/table[@class='wikitable']|/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/div[@class='rellink boilerplate seealso']")

	pairs = zip(states,other,tables)

	stateresults=[]
	for state,other,tab in pairs[:46]:
		newstate = dict()
		newstate['name']=state.xpath("span[@class='mw-headline']/a")[0].text
		logging.debug('Parsing state: %s' % newstate['name'])
		newstate['votes']=int(other.xpath("b[1]/text()")[0].split(' ')[0])
		data = map(lambda x:getpcts(x[2:]),compress(other.xpath("text()"),[0,1,0,1]))
		newstate['2004']=(other.xpath("a[1]/text()")[0].split(' ')[0],data[0])
		newstate['2008']=(other.xpath("a[2]/text()")[0].split(' ')[0],data[1])
		polls = []
		for i,row in enumerate(tab.xpath("tr")[1:]):
			if len(row.xpath("td/a|td/br"))>2:
				newpoll = dict()
				newpoll['pollers'] = map(lambda x:x.strip(),row.xpath("td[1]/a/text()"))
				newpoll['url'] = row.xpath("td[1]/a/@href")
				dates = getDateSpan(row.xpath("td[2]/text()"))
				newpoll['fromDate'] = dates.startDate
				newpoll['toDate'] = dates.endDate
				samplesize = filter(lambda x:samplere.match(x.strip()),list(row.xpath("td[1]")[0].itertext()))[0]
				sampleresult = samplere.match(samplesize.strip().replace(',',''))
				newpoll['size'] = sampleresult.group('size')
				newpoll['votertype'] = sampleresult.group('votertype') or 'UK'
				if newpoll['votertype'] in ['n/a']:
					newpoll['votertype'] = 'UK'
				margininput = filter(lambda x:marginre.match(x.strip()),list(row.xpath("td[1]")[0].itertext()))
				if len(margininput)>0:
					newpoll['margin']=float(marginre.match(margininput[0].strip()).group('margin'))
				else:
					newpoll['margin']=float(0)
				polls.append(newpoll)
				pollresults = getpollresults(row,True)
				if pollresults['republican'] == 'Mitt Romney':
					newpoll['results'] = pollresults
			elif len(row.xpath("td/p/a|td/p/br"))>2:
				newpoll = dict()
				newpoll['pollers'] = map(lambda x:x.strip(),row.xpath("td[1]/p/a/text()"))
				newpoll['url'] = row.xpath("td[1]/p/a/@href")
				dates = getDateSpan(row.xpath("td[2]/text()"))
				newpoll['fromDate'] = dates.startDate
				newpoll['toDate'] = dates.endDate
				samplesize = filter(lambda x:samplere.match(x.strip()),list(row.xpath("td[1]/p")[0].itertext()))[0]
				sampleresult = samplere.match(samplesize.strip().replace(',',''))
				margininput = filter(lambda x:marginre.match(x.strip()),list(row.xpath("td[1]/p")[0].itertext()))
				if len(margininput)>0:
					newpoll['margin']=float(marginre.match(margininput[0].strip()).group('margin'))
				else:
					newpoll['margin']=float(0)
				newpoll['size'] = sampleresult.group('size')
				newpoll['votertype'] = sampleresult.group('votertype') or 'UK'
				if newpoll['votertype'] in ['n/a']:
					newpoll['votertype'] = 'UK'
					polls.append(newpoll)
				pollresults = getpollresults(row,True)
				if pollresults['republican'] == 'Mitt Romney':
					newpoll['results'] = pollresults			
			else:
				pollresults = getpollresults(row,False)
				if pollresults['republican'] == 'Mitt Romney':
					newpoll['results'] = pollresults


		newstate['polls']=polls
		stateresults.append(newstate)
	Poll(id='us_state_2012',poll=stateresults).put()