# -*- coding:utf8 -*-
import tornado.web

from worker import AsyncRedPacket


class RedPacketPresent(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self, red_id):
        response = '0'
        try:
            args = dict(
                red_id=red_id,
                month=self.get_argument('month', None),
                action_type=self.get_argument('action_type', None),
            )
            response = AsyncRedPacket().process(args)
        except Exception, ex:
            response = ''.join(['ex post: ', ex.message])
        finally:
            self.write(response if response is not None else 'None')
            self.finish()
