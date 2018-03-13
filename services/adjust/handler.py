# -*- coding:utf8 -*-
import tornado.web
from worker import Adjust


class AdjustBT(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        response = '0'
        try:
            param = self.request.body
            response = Adjust().deposit(param)
        except Exception, ex:
            print 'ex', ex.message
            response = ''.join(['ex post: ', ex.message])
        finally:
            self.write(response if response is not None else 'None')
            self.finish()


class AdjustReverse(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        response = '0'
        try:
            param = self.request.body
            response = Adjust().reverse(param)
        except Exception, ex:
            print 'ex', ex.message
            response = ''.join(['ex post: ', ex.message])
        finally:
            self.write(response if response is not None else 'None')
            self.finish()
