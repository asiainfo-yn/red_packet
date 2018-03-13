# -*- coding: UTF-8 -*-
from os import environ
from dict4ini import *
import logging
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import urllib
import urllib2
import ujson
import gevent
from gevent import monkey, pool

monkey.patch_all()

url_header = 'http://localhost:8100/acct/trust-alipay/cash/acct_id/'

packet_name = 'alipay_bill'
FORMAT = '%(asctime)s %(process)d %(name)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, filename=''.join([packet_name, '.log']))
logger = logging.getLogger(packet_name)

g_len = 0
son_objects = []


class Owe(object):
    def __init__(self):
        self.billing_cycle_id = None
        self.amount = None
        self.acct_id = None


def process(owe):
    global g_len, son, son_objects

    try:
        url = ''.join([url_header, str(owe.acct_id)])
        request_content = dict(billing_cycle_id=owe.billing_cycle_id, amount=owe.amount)

        req = urllib2.Request(url, data=urllib.urlencode(request_content))
        response = urllib2.urlopen(req)
        res = ujson.loads(response.read())

        print res
    except Exception, ex:
        logger.error(
            ''.join([
                str(owe.acct_id), ':',
                str(ex.message),
            ])
        )
    finally:
        g_len += 1
        if g_len % 1000 == 0:
            logger.info('g_len=%d' % g_len)


def start():
    global son

    try:
        #
        p = pool.Pool(1)
        jobs = []

        o = Owe()
        o.acct_id = 413899300
        o.billing_cycle_id = 11709
        o.amount = 3
        for pay in [o]:
            jobs.append(p.spawn(process, pay))
            break
        gevent.joinall(jobs)

        son.add_all(son_objects)
        son.commit()
    except Exception, ex:
        logger.error(ex.message)

    return 'pool tasks finished'


if __name__ == '__main__':
    """
    后付费用户支付宝托收和销账程序
    """
    secretKey = environ.get('LINKAGE_KEY')
    config = dict4ini.DictIni('access_config.ini', secretKey=secretKey).dict()
    db_conf = config.get('DB_ORACLE').get('ACCT_T5')
    conn_str = ''.join([
        'oracle://',
        db_conf['user'], ':',
        db_conf['password'], '@',
        db_conf['tns']
    ])
    engine = sqlalchemy.create_engine(conn_str, encoding='gbk', echo=True)
    Session = sessionmaker(bind=engine)
    son = Session()

    logger.info(start())
    son.close()
