#!/usr/bin/python

from lxml import etree
import re
from itertools import compress
from pprint import pprint
from dateprocessing import getDateSpan,DateFromTo
from datejsondecoder import dumps

tree = etree.parse("original3.html",etree.HTMLParser())

states = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/h3")
other = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/p")[1:]
tables = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/table[@class='wikitable']|/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/div[@class='rellink boilerplate seealso']")

pairs = zip(states,other,tables)

pctre = re.compile('(\d+|\d+\.\d+)\%.(\d+|\d+\.\d+)\%')

samplere = re.compile('.*Sample size: ?(?P<size>Varies|\d+)-?\d* ?(?P<votertype>LV|RV)? ?.*')

marginre = re.compile('.*Margin of error(: .| .* )(?P<margin>\d+|\d+.\d+)%.*')

def getpcts(raw):
	d = pctre.match(raw)
	return float(d.group(1)),float(d.group(2))

stateresults=[]

def getpollresults(row,isfirst):
	democrat = None
	demopct = None
	republic = None
	repubpct = None
	leadmargin = None
	if isfirst:
		democrat = row.xpath("td[3]/text()|td[3]/a/text()|td[3]/a/b/text()|td[3]/b/a/text()|td[3]/b/text()")[0]
		demopct = row.xpath("td[4]/text()|td[4]/a/text()|td[4]/a/b/text()|td[4]/b/a/text()|td[4]/b/text()")[0]
		republican = row.xpath("td[5]/text()|td[5]/a/text()|td[5]/a/b/text()|td[5]/b/a/text()|td[5]/b/text()")[0]
		repubpct = row.xpath("td[6]/text()|td[6]/a/text()|td[6]/a/b/text()|td[6]/b/a/text()|td[6]/b/text()")[0]
		leadmargin = row.xpath("td[7]/text()|td[7]/a/text()|td[7]/a/b/text()|td[7]/b/a/text()|td[7]/b/text()")[0]
	else:
		democrat = row.xpath("td[1]/text()|td[1]/a/text()|td[1]/a/b/text()|td[1]/b/a/text()|td[1]/b/text()")[0]
		demopct = row.xpath("td[2]/text()|td[2]/a/text()|td[2]/a/b/text()|td[2]/b/a/text()|td[2]/b/text()")[0]
		republican = row.xpath("td[3]/text()|td[3]/a/text()|td[3]/a/b/text()|td[3]/b/a/text()|td[3]/b/text()")[0]
		repubpct = row.xpath("td[4]/text()|td[4]/a/text()|td[4]/a/b/text()|td[4]/b/a/text()|td[4]/b/text()")[0]
		leadmargin = row.xpath("td[5]/text()|td[5]/a/text()|td[5]/a/b/text()|td[5]/b/a/text()|td[5]/b/text()")[0]
	return (democrat,float(demopct[:-1]),republican,float(repubpct[:-1]),float(leadmargin) if leadmargin not in ['Tie','Tied'] else 0.0)


for state,other,tab in pairs[:46]:
	newstate = dict()
	newstate['name']=state.xpath("span[@class='mw-headline']/a")[0].text
	newstate['votes']=int(other.xpath("b[1]/text()")[0].split(' ')[0])
	data = map(lambda x:getpcts(x[2:]),compress(other.xpath("text()"),[0,1,0,1]))
	newstate['2004']=(other.xpath("a[1]/text()")[0].split(' ')[0],data[0])
	newstate['2008']=(other.xpath("a[2]/text()")[0].split(' ')[0],data[1])
	polls = []
	for row in tab.xpath("tr")[1:]:
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
			newpoll['votertype'] = sampleresult.group('votertype')
			margininput = filter(lambda x:marginre.match(x.strip()),list(row.xpath("td[1]")[0].itertext()))
			if len(margininput)>0:
				newpoll['margin']=float(marginre.match(margininput[0].strip()).group('margin'))
			else:
				newpoll['margin']=float(0)
			polls.append(newpoll)
			pollresults = getpollresults(row,True)
			if pollresults[2] == 'Mitt Romney':
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
			newpoll['votertype'] = sampleresult.group('votertype')
			polls.append(newpoll)
			pollresults = getpollresults(row,True)
			if pollresults[2] == 'Mitt Romney':
				newpoll['results'] = pollresults			
		else:
			pollresults = getpollresults(row,False)
			if pollresults[2] == 'Mitt Romney':
				newpoll['results'] = pollresults


	newstate['polls']=polls
	stateresults.append(newstate)


#pprint(stateresults)
print dumps(stateresults)