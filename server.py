from datetime import datetime
import tornado.web
import pymongo
import bson
import time
import os
import simplejson as json
from tornad_io import SocketIOHandler
from tornad_io import SocketIOServer
import random

class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the dashboard page"""
    def get(self):
        self.render("index.html")


class InboundHandler(tornado.web.RequestHandler):
    """ Receive new messages """
    def post(self):
        msg = {
            'dated': time.time(),
            'source': self.get_argument('source'),
            'from': self.get_argument('from'),
            'profile_image': self.get_argument('profile_image'),
            'message': self.get_argument('message'),
            'url': self.get_argument('url'),
            'votes': 0}

        uid = mc.raw.insert(msg)
        msg['id'] = str(uid)
        msg['_id'] = None

        mjson = json.dumps({'type': 'msg', 'channel': 'raw', 'm': msg})

        for p in participants:
            if (random.randint(0,8) == 0):
                p.send(mjson)

        self.write(json.dumps({'status': 'ok'}))

class UpdateHandler(tornado.web.RequestHandler):
    def post(self):
        id = bson.objectid.ObjectId(self.get_argument('id'))
        tag = self.get_argument('tag','')
        mc.raw.update({'_id': id}, {'$inc': {'votes': 1}, '$set': {'tag': tag}})
        msg = mc.raw.find_one({'_id': id})

        msg['id'] = str(msg['_id'])
        msg['_id'] = None

        if msg['votes'] == 1:
            for p in participants:
                p.send(json.dumps({'type': 'msg', 'channel': 'filtered', 'm': msg}))

        self.write(json.dumps({'status': 'ok'}))                


participants = set()
mongo_connection = pymongo.Connection()
mc = mongo_connection['twicks']

mc.raw.ensure_index([('dated',pymongo.DESCENDING)])
mc.raw.ensure_index([('m.tag',pymongo.DESCENDING)])

class MessageHandler(SocketIOHandler):
    def on_open(self, *args, **kwargs):
        """ Register participant """
        participants.add(self)
        for m in mc.raw.find().sort([('dated', -1)]).limit(50):
            m['id'] = str(m['_id'])
            m['_id'] = None
            j = None
            try:
                j = json.dumps({'type': 'msg', 'channel': 'raw', 'm': m})
                self.send(j)
            except Exception,e:
                pass
        # Send welcome

    def on_message(self, message):
        """ Uprate a message """
        pass

    def on_close(self):
        """ Remove participant """
        participants.remove(self)

#use the routes classmethod to build the correct resource
msg_route = MessageHandler.routes("socket.io/*")

#configure the Tornado application
application = tornado.web.Application(
    [(r"/", IndexHandler), (r"/post", InboundHandler), (r"/update", UpdateHandler), msg_route],
    enabled_protocols = ['websocket', 'flashsocket', 'xhr-multipart', 'xhr-polling'],
    flash_policy_port = 8043,
    flash_policy_file = 'flashpolicy.xml',
    socket_io_port = 8888,
    static_path = os.path.join(os.path.dirname(__file__), "static")
)

if __name__ == "__main__":
    socketio_server = SocketIOServer(application) #spin up the server
