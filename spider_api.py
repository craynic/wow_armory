#!/usr/bin/env python
# coding: utf-8

import urllib2
import ConfigParser
import json
import time
import random
import pymongo
import fake_useragent

def get_json(url):
	print 'Fetching:', url
	while True:
		time.sleep(1)
		try:
			request = urllib2.Request(url)
			page = urllib2.urlopen(request)
		except Exception as e:
			print e
		else:
			try:
				j = json.loads(page.read())
			except Exception as e:
				print e
			else:
				if j.has_key('lastModified'):
					return j
				elif j.has_key('reason'):
					print 'Error: %s' % j['reason'],
					if j['reason'].find(' not found.') >= 0:
						print ''
						return None
				elif j == {}:
					print 'Error: empty json.'
					return None
				else:
					print 'Unkown error.',
		print 'Try again.'
		time.sleep(random.random()*5)
			
class spider:
	def __init__(self):
		print 'Reading configurations...',
		config = ConfigParser.ConfigParser()
		config.read(["spider.default.cfg", "spider.cfg"])
		self.config = config
		print 'Done.' 
		print 'Preparing fake_useragent...',
		_ua = fake_useragent.UserAgent()
		print 'Done.'
		
	def spide(self):
		
		c = self.config
		
		print 'Connecting to mongodb at %s on %s ...' % (c.get('mongodb', 'domain'), c.getint('mongodb', 'port')),
		try:
			mongodb = pymongo.MongoClient(c.get('mongodb', 'domain'), c.getint('mongodb', 'port'))
		except Exception as e:
			print 'Failed.'
			print e
			return
		else:
			print 'Done.'
		print 'Using db %s, collection %s....' % (c.get('mongodb', 'db'), c.get('mongodb', 'collection')),
		try:
			dbc = mongodb[c.get('mongodb', 'db')][c.get('mongodb', 'collection')]
		except Exception as e:
			print 'Failed.'
			print e
			return
		else:
			print 'Done.'
			
		domain = c.get('source', 'domain')
		realm = c.get('source', 'realm').replace(' ', '%20')
		guild = c.get('source', 'guild').replace(' ', '%20')
		protocol = c.get('source', 'protocol') + '://'
		guild_url = '%s%s/api/wow/guild/%s/%s?fields=members' %\
			(protocol, domain, realm, guild)
		gj = get_json(guild_url)
		for person in gj['members']:
			i = dbc.find({'name':person['character']['name'].encode('utf-8')})
			if i.count() > 0:
				continue
			info = {}
			character = person['character']
			info['name'] = character['name'].encode('utf-8')
			info['race'] = character['race']
			info['class'] = character['class']
			info['gender'] = character['gender']
			info['level'] = character['level']
			info['realm'] = character['guildRealm'].encode('utf-8')
			info['guild'] = character['guild'].encode('utf-8')
			if info['level'] >= c.getint('default', 'max_level'):
				chara_url = '%s%s/api/wow/character/%s/%s?fields=items,professions,pvp' %\
					(protocol, domain, realm, info['name'])
				cj = get_json(chara_url)
				if cj != None:
					info['item_level'] = cj['items']['averageItemLevel']
					prof = []
					for i in cj['professions']['primary']:
						prof.append(i['name'].encode('utf-8'))
					info['profession'] = prof
					info['personal_rating'] = cj['pvp']["brackets"]["ARENA_BRACKET_RBG"]["rating"]
			dbc.insert(info)

if __name__ == '__main__':
	s = spider()
	s.spide()
