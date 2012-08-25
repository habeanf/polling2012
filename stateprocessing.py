from lxml import etree
import re
from itertools import compress

tree = etree.parse("original.html",etree.HTMLParser())

states = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/h3")
other = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/p")[1:]
tables = tree.xpath("/html/body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/table[@class='wikitable']")

pairs = zip(states,other,tables)

pctre = re.compile('(\d+|\d+\.\d+)\%.(\d+|\d+\.\d+)\%')

samplere = re.compile('.*Sample size: ?(?P<size>Varies|\d+)-?\d* ?(?P<votertype>LV|RV)? ?.*')

marginre = re.compile('.*Margin of error(: .| .* )(?P<margin>\d+|\d+.\d+)%.*')

def getpcts(raw):
	d = pctre.match(raw)
	return float(d.group(1)),float(d.group(2))

stateresults=[]

for state,other,tab in pairs[:46]:
	newstate = dict()
	newstate['name']=state.xpath("span[@class='mw-headline']/a")[0].text
	newstate['votes']=int(other.xpath("b[1]/text()")[0].split(' ')[0])
	print state.xpath("span[@class='mw-headline']/a")[0].text
	data = map(lambda x:getpcts(x[2:]),compress(other.xpath("text()"),[0,1,0,1]))
	newstate['2004']=(other.xpath("a[1]/text()")[0].split(' ')[0],data[0])
	newstate['2004']=(other.xpath("a[2]/text()")[0].split(' ')[0],data[1])
	polls = []
	for row in tab.xpath("tr")[1:]:
		if len(row.xpath("td/a|td/br"))>2:
			newpoll = dict()
			newpoll['pollers'] = map(lambda x:x.strip(),row.xpath("td[1]/a/text()"))
			newpoll['url'] = row.xpath("td[1]/a/@href")
			newpoll['date struct'] = row.xpath("td[2]/text()")
 			print map(lambda x:x.strip(),row.xpath("td[1]/a/text()")),
			print row.xpath("td[2]/text()")
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
		if len(row.xpath("td/p/a|td/p/br"))>2:
			newpoll = dict()
			newpoll['pollers'] = map(lambda x:x.strip(),row.xpath("td[1]/p/a/text()"))
			newpoll['url'] = row.xpath("td[1]/p/a/@href")
			newpoll['date struct'] = row.xpath("td[2]/text()")
			print map(lambda x:x.strip(),row.xpath("td[1]/p/a/text()")),
			print row.xpath("td[2]/text()")
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
		
	newstate['polls']=polls
	stateresults.append(newstate)

#print stateresults