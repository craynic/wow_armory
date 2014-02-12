import urllib2
import bs4
import random
import pymongo
from string import atoi
import time

def make_headers():
	return {'User-Agent':random.choice(ua_list)}
	
def get_chara(url):
	
	req = urllib2.Request(url, headers = make_headers())
	try:
		page = urllib2.urlopen(req).read()
	except:
		print url
		return None
		
	soup = bs4.BeautifulSoup(page)
	if None != soup.find('div', {'id':'server-error'}):
		return None
	itemlvl = soup.find('div', {'id':'summary-averageilvl-best'}).contents[0]
	profs = soup.find('div', {'class':'summary-professions'}).\
		findAll('span', {'class':'name'})
	prof1 = profs[0].contents[0]
	prof2 = profs[1].contents[0]
	bgrating = soup.find('div', {'class':'summary-battlegrounds'}).\
		find('li', {'class':'rating'}).\
		find('span', {'class':'value'}).\
		contents[0]
	
	time.sleep(random.random()*3)
	return {'itemlvl':atoi(itemlvl), 'prof1':prof1, 'prof2':prof2, 'bgrating':bgrating}
	
def main():
	
	base_URL = raw_input("URL for guild: ")
	if base_URL[-1] != '/':
		base_URL = base_URL + '/'
	rost_URL = base_URL + "roster"
	req = urllib2.Request(rost_URL, headers = make_headers())
	mongodb = pymongo.MongoClient()
	dbc = mongodb['wow']['armory']
	
	while True:
		try:
			page = urllib2.urlopen(req).read()
		except:
			print 'page unavailable.'
			break
			
		soup = bs4.BeautifulSoup(page)
		souptmp = soup.find('div', {'id':'roster'})
		lines = souptmp.find_all('tr', {'class':['row1','row2']})
		
		for line in lines:
			name = line.find('td', {'class':'name'}).find('a').contents[0]
			lvl = line.find('td', {'class':'lvl'}).contents[0]
			cls = line.find('td', {'class':'cls'}).find('span').get('data-tooltip')
			race = line.find('td', {'class':'race'}).find('span').get('data-tooltip')
			post = {"name":name, "race":race, "class":cls, "level":atoi(lvl)}
			print name, race, cls, lvl
			if atoi(lvl) == 90:
				chara_URL = ('http://www.battlenet.com.cn' + line.find('td', {'class':'name'}).find('a').get('href')).encode('utf-8')
				d = get_chara(chara_URL)
				if d != None:
					post['item_level'] = d['itemlvl']
					post['profession1'] = d['prof1']
					post['profession2'] = d['prof2']
					post['bg_rating'] = d['bgrating']
			#dbc.update(post, {}, upsert = True)
			dbc.insert(post)
		
		souptmp = soup.find('a', {'class':'page-next'})
		if souptmp == None:
			break
		page_URL = souptmp.get('href')
		req = urllib2.Request(rost_URL + page_URL, headers = make_headers())
	
	print dbc.find().count()

if __name__ == '__main__':
	if 'ua_list' not in dir():
		ua_list = ['Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36' \
'Mozilla/5.0 (Windows NT 5.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1.0.1 Safari/537.36; SWRInfo: 1001:vbox.com:administrator', \
'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322)', \
'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.76 Safari/537.36', \
'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36', \
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.76 Safari/537.36', \
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.73.11 (KHTML, like Gecko) Version/6.1.1 Safari/537.73.11', \
'Opera/9.80 (X11; Linux i686) Presto/2.12.388 Version/12.16', \
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0', \
'Mozilla/5.0 (Windows NT 6.1; rv:26.0) Gecko/20100101 Firefox/26.0', \
'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; Maxthon)']	
	main()
