"""
Twitter submitter

"""
import time
import simplejson
import pprint
import urllib2, urllib
import random
import re

class TwitterSearch(object):
    last_id = None
    term = None

    def __init__(self, term):
        self.term = term

    def fetch(self, limit=1):
        """
        Search
        """
        
        query = dict(q=self.term, result_type='recent', rpp="100")
        if self.last_id:
            query['since_id'] = self.last_id
	try:
        	fh = urllib2.urlopen('http://search.twitter.com/search.json?%s' % urllib.urlencode(query))
	except Exception, e:
		time.sleep(60)
		return []
        result = simplejson.load(fh)
        
        for r in result['results']:
            max_id = r.get('id',0)
            if self.last_id is None or max_id > self.last_id:
                self.last_id = max_id
        
        return result['results']
        
        
ts = TwitterSearch('#eqnz OR earthquake')

pre_load = dict()

while True:

    messages = []

    for r in ts.fetch():
        messages.append(r)


    waiting = 0.0


    for r in messages:
        print "Sending new entry: %s" % r['text'].encode('ascii','ignore')
        urllib2.urlopen('http://127.0.0.1:8888/post',urllib.urlencode({'source': 'twitter', 'from': r['from_user'], 'profile_image': r['profile_image_url'], 'message': r['text'].encode('ascii','ignore'), 'url': 'x'}))
        time.sleep(15.0/len(messages))
        waiting += 15.0/len(messages)
        #conn.send(simplejson.dumps(r), destination='/topic/%s' % channel)
        

    #conn.send(simplejson.dumps(dict(text="Happy test test", from_user="testtwitter", profile_image_url="http://s3.amazonaws.com/twitter_production/profile_images/186623658/hari_normal.jpg")), destination="/topic/twitter")
    
    if waiting < 15.0:
        print "Waiting %0.2fs til recall" % waiting
        time.sleep(15.0-waiting)

    #time.sleep(random.randint(30,60))



"""

conn.send('testing testing', destination='/topic/twitter')
time.sleep(1)
conn.disconnect()

"""
