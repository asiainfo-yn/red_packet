# -*- coding: UTF-8 -*-
from os import environ
from dict4ini import *
from datetime import *
import logging
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from services.red_packet.modules import *
from services.red_packet.errors import *
from defines.variables import *
import urllib
import urllib2
import gevent
from gevent import monkey, pool

monkey.patch_all()


# url_header = 'http://135.32.8.70/acct/red-packet/user/'
url_header = 'http://localhost:8100/acct/red-packet/user/'

packet_name = 'packet_bs'
FORMAT = '%(asctime)s %(process)d %(name)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, filename=''.join([packet_name, '.log']))
logger = logging.getLogger(packet_name)
g_len = 0
billing_cycles = None


def process(red_id):
    global g_len, billing_cycles

    try:
        packets = map(lambda b: dict(
            red_id=red_id, acct_month=b.cycle_begin_date.strftime('%Y%m')
        ), billing_cycles)

        packets = sorted(packets, key=lambda m: m.get('acct_month'))
        for packet in packets:
            acct_month = packet.get('acct_month')

            url = ''.join([url_header, str(red_id)])
            request_content = dict(month=acct_month, action_type=ACTION_TYPE_BS)

            req = urllib2.Request(url, data=urllib.urlencode(request_content))
            response = urllib2.urlopen(req)
            res = ujson.loads(response.read())

            if res.get('RESULT_CODE') != HasRecord().code:
                logger.info(
                    ''.join([
                        str(red_id), ':',
                        acct_month, ':',
                        str(res.get('RESULT_CODE')), '-', res.get('RESULT_MSG')
                    ])
                )
    except Exception, ex:
        logger.error(
            ''.join([
                str(red_id), ':',
                str(ex.message),
            ])
        )
    finally:
        g_len += 1
        if g_len % 1000 == 0:
            logger.info('g_len=%d' % g_len)


def start():
    global son, billing_cycles

    try:
        # 取前三个月账期
        cur_month = datetime.strftime(datetime.now(), '%Y%m')
        cur_cycle = ''.join(['1', str(cur_month)[2:]])
        billing_cycles = son.query(BillingCycle).filter(
            BillingCycle.billing_cycle_id < cur_cycle,
            BillingCycle.billing_cycle_id >= MIN_BILLING_CYCLE,
        ).order_by(BillingCycle.billing_cycle_id.desc()).limit(LIMIT_MONTH).all()

        # 补送红包表
        bs = son.query(ARedPacketBs).filter(
            ARedPacketUser.red_id == ARedPacketBs.red_id
        )

        packet_users = son.query(
            ARedPacketUser
        ).filter(
            ARedPacketUser.finish_flag == FINISH_FLAG_NORMAL,
            bs.exists(),
        ).all()

        logger.info('len(packet_list)=%d' % len(packet_users))

        p = pool.Pool(500)
        jobs = []

        for user in packet_users:
            jobs.append(p.spawn(process, user.red_id))

        gevent.joinall(jobs)
    except Exception, ex:
        logger.error(ex.message)

    return 'pool tasks finished'


if __name__ == '__main__':
    """
    补送红包，每天运行一次
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
    engine = sqlalchemy.create_engine(conn_str, encoding='gbk', echo=False)
    Session = sessionmaker(bind=engine)
    son = Session()

    logger.info(start())
    son.close()
