#!/usr/bin/env python
# coding: utf-8

import urllib2
import ConfigParser
import json
import time
import random
import pymongo
import fake_useragent

def init():
	print 'Reading configurations...',
	config = ConfigParser.ConfigParser()
	config.read(["spider.cfg", "spider_default.cfg"])
	global _domain, _language, _realm, _guild, _protocol, _max_level, _output, _ua
	_domain = config.get('default', 'domain')
	_language = config.get('default', 'language')
	_realm = config.get('default', 'realm')
	_guild = config.get('default', 'guild')
	_protocol = config.get('default', 'protocol') + r'://'
	_max_level = config.getint('default', 'max_level')
	_output = False
	print 'Done.' 
	print 'Preparing fake_useragent...',
	_ua = fake_useragent.UserAgent()
	print 'Done.'
	
def get_json(url):
	if not _output:
		print 'Fetching:', url
	while True:
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
		time.sleep(random.random()*5+1)
	
def main():
	print 'Connect to mongodb...',
	try:
		mongodb = pymongo.MongoClient()
		dbc = mongodb['wow']['lastcampaign']
	except:
		print 'Failed.'
		print 'Output to stdout.'
		_output = True
	else:
		print 'Done.'
	realm = _realm.replace(' ', '%20')
	guild = _guild.replace(' ', '%20')
	guild_url = '%s%s/api/wow/guild/%s/%s?fields=members' %\
		(_protocol, _domain, realm, guild)
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
		if info['level'] >= _max_level:
			chara_url = '%s%s/api/wow/character/%s/%s?fields=items,professions,pvp' %\
				(_protocol, _domain, realm, info['name'])
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
	init()
	main()
