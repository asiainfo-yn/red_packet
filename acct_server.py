# -*- coding:utf8 -*-
import os.path
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
from tornado.process import fork_processes, cpu_count
from tornado.options import define, options

from services.red_packet.handler import *
from services.trust_alipay.handler import *
from services.adjust.handler import *

define("port", default=8100, type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/acct/red-packet/user/(\d+)", RedPacketPresent),
            (r"/acct/trust-alipay/trust/acct_id/(\d+)", AlipayTrust),
            (r"/acct/trust-alipay/cash/acct_id/(\d+)", AlipayCash),
            (r"/acct/adjust/cash/", AdjustBT),
        ]

        settings = {
            'debug': False,
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            'template_path': os.path.join(os.path.dirname(__file__), "templates")
        }
        super(Application, self).__init__(handlers=handlers, **settings)


if __name__ == '__main__':
    print('http://localhost:8100/acct/red-packet/user/123')
    print('python acct_server.py -log_file_prefix=8100.log')
    print('python acct_server.py -port=8100 -log_file_prefix=server.8100.log')

    options.parse_command_line()
    app = Application()
    sockets = tornado.netutil.bind_sockets(options.port)
    # fork_processes(cpu_count())
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()
