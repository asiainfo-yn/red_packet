# -*- coding:utf8 -*-
import tornado.web
'''
from multiprocessing.managers import EventProxy
from multiprocessing import Event
from multiprocessing.managers import BaseManager
'''
from worker import AsyncTrustAlipay

'''
class QueueManager(BaseManager): pass
QueueManager.register('s_pipe')
QueueManager.register('r_pipe')
QueueManager.register('get_queue')
m = QueueManager(address=('localhost', 50000), authkey='abracadabra')
m.connect()
s = m.s_pipe()
'''

# q = tornado.queues.Queue(10)


class AlipayTrust(tornado.web.RequestHandler):
    '''
    @tornado.gen.coroutine
    def async_task(self, args):
        q.put(args)
        # return s.send(args)
        # return self.application.pool.apply_async(async_func, [AsyncTrustAlipay, args], callback=test_func)
    '''

    @tornado.web.asynchronous
    # @tornado.gen.engine
    def post(self, acct_id):
        response = '0'
        try:
            args = dict(
                acct_id=acct_id,
            )
            response = AsyncTrustAlipay().process_trust(args)

            # result = yield tornado.gen.Task(self.async_task, args)
            # response = yield q.get()
            # response = result.get()
            # response = args
        except Exception, ex:
            print 'ex', ex.message
            response = ''.join(['ex post: ', ex.message])
        finally:
            self.write(response if response is not None else 'None')
            self.finish()


class AlipayCash(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self, acct_id):
        response = '0'
        try:
            args = dict(
                acct_id=acct_id,
                billing_cycle_id=self.get_argument('billing_cycle_id', None),
                amount=self.get_argument('amount', None),
            )
            response = AsyncTrustAlipay().process_cash_bill(args)

            # result = yield tornado.gen.Task(self.async_task, args)
            # response = yield q.get()
            # response = result.get()
            # response = args
        except Exception, ex:
            print 'ex', ex.message
            response = ''.join(['ex post: ', ex.message])
        finally:
            self.write(response if response is not None else 'None')
            self.finish()
