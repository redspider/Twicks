from datetime import datetime
import tornado.web
import tornado.websocket
import tornado.ioloop
import pymongo
import bson
import time
import os
import simplejson as json
import tornadio
import tornadio.router
import tornadio.server
#from tornadio import SocketIOHandler
#from tornadio import SocketIOServer
import random
from md5 import md5
import logging
log = logging.getLogger()

logging.getLogger().setLevel(logging.DEBUG)

ucheck = dict()

def normalise(s):
    s = s.replace(r'RT @[^ ]+','')
    s = s.lower()
    s = s.strip()
    return md5(s).hexdigest()

class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the dashboard page"""
    def get(self):
        self.render("index.html")


class InboundHandler(tornado.web.RequestHandler):
    """ Receive new messages """
    def post(self):
        global ucheck

        msg = {
            'dated': time.time(),
            'source': self.get_argument('source'),
            'from': self.get_argument('from'),
            'profile_image': self.get_argument('profile_image'),
            'message': self.get_argument('message'),
            'url': self.get_argument('url'),
            'votes': 0,
            'key': normalise(self.get_argument('message'))
        }

        #if ucheck.has_key(msg['key']) and ((time.time() - ucheck[msg['key']]) > 1200):
        if ucheck.has_key(msg['key']) and ((time.time() - ucheck[msg['key']]) > 1200):

            # If message has already been through and 20 minutes has passed.
            log.debug("Ignored key %s (%s)" % (msg['key'], msg['message']))
            return
        
        if not ucheck.has_key(msg['key']):
            ucheck[msg['key']] = time.time()

        uid = mc.raw.insert(msg)
        msg['id'] = str(uid)
        msg['_id'] = None
        msg['user_count'] = len(participants)

        mjson = {'type': 'msg', 'channel': 'raw', 'm': msg}

        for p in participants:
            if ((time.time() - p.last_message) > float(p.rate)):
                p.last_message = time.time()
                p.send(mjson)
            if (time.time() - p.last_received) > 120:
                log.debug("Timeout")
                participants.remove(p)
                #p.connection.end()

        self.write(json.dumps({'status': 'ok'}))

class UpdateHandler(tornado.web.RequestHandler):
    def post(self):
        id = bson.objectid.ObjectId(self.get_argument('id'))
        tag = self.get_argument('tag','')
        mc.raw.update({'_id': id}, {'$inc': {'votes': 1}, '$set': {'tag': tag}})
        msg = mc.raw.find_one({'_id': id})

        msg['id'] = str(msg['_id'])
        msg['_id'] = None
        msg['user_count'] = len(participants)

        if msg['votes'] == 1:
            for p in participants:
                p.send({'type': 'msg', 'channel': 'filtered', 'm': msg})

        self.write(json.dumps({'status': 'ok'}))                


participants = set()
mongo_connection = pymongo.Connection()
mc = mongo_connection['twicks']

mc.raw.ensure_index([('dated',pymongo.DESCENDING)])
mc.raw.ensure_index([('tag',pymongo.DESCENDING)])

class MessageHandler(tornado.websocket.WebSocketHandler):
    def send(self, message):
        m = json.dumps(message)
        try:
            self.write_message(m)
        except IOError, e:
            pass

    def open(self, *args, **kwargs):
        """ Register participant """
        global participants
        log.debug("New client")

        self.send({'type':'welcome', 'message': 'Connected!'})
        log.debug("Sent connected message")

        if len(participants) > 120:
            log.debug("Server full")
            self.send({'type': 'error', 'message': 'Sorry the server is full right now'})
            return

        self.last_message = time.time()
        self.last_received = time.time()
        self.rate = 2
        for m in mc.raw.find().sort([('dated', -1)]).limit(20):
            m['id'] = str(m['_id'])
            m['_id'] = None
            m['user_count'] = len(participants)
            j = None
            try:
                self.send({'type': 'msg', 'channel': 'raw', 'm': m})
            except Exception,e:
                pass

        for tag in ['damage','advice','requests']:
            messages = list(mc.raw.find({'tag': tag}).sort([('dated', -1)]).limit(50))
            for m in messages[::-1]:
                m['id'] = str(m['_id'])
                m['_id'] = None
                m['user_count'] = len(participants)

                j = None
                try:
                    self.send({'type': 'msg', 'channel': 'raw', 'm': m})
                except Exception,e:
                    pass

        participants.add(self)
        

    def on_message(self, message):
        """ Uprate a message """
        global participants

        m = json.loads(message)
        self.last_received = time.time()

        if (m['type'] == 'options'):
            log.debug("Changed client rate to %d" % int(m['rate']))
            self.rate = int(m['rate'])

    def on_close(self):
        """ Remove participant """
        global participants
        
        log.debug("Removed client")
        participants.remove(self)



#configure the Tornado application
application = tornado.web.Application(
    [(r"/", IndexHandler), (r"/post", InboundHandler), (r"/update", UpdateHandler), (r"/ws",MessageHandler)],
    enabled_protocols = ['websocket'],
    static_path = os.path.join(os.path.dirname(__file__), "static")
)

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()