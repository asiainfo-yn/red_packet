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

packet_name = 'packet_all'
FORMAT = '%(asctime)s %(process)d %(name)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, filename=''.join([packet_name, '.log']))
logger = logging.getLogger(packet_name)
billing_cycles = None
g_len = 0


def process(red_id):
    """
    红包一定要按月份从低到高送
    :param red_id:
    :return:
    """
    global billing_cycles, g_len

    try:
        packets = map(lambda b: dict(
            red_id=red_id, acct_month=b.cycle_begin_date.strftime('%Y%m')
        ), billing_cycles)

        packets = sorted(packets, key=lambda m: m.get('acct_month'))
        for packet in packets:
            acct_month = packet.get('acct_month')

            url = ''.join([url_header, str(red_id)])
            request_content = dict(month=acct_month, action_type=ACTION_TYPE_ALL)

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
                str(ex.args[0].errno), ':', ex.args[0].strerror
            ])
        )
    finally:
        g_len += 1
        if g_len % 1000 == 0:
            logger.info('g_len=%d' % g_len)


def start():
    global son, billing_cycles

    # 取前三个月账期
    cur_month = datetime.strftime(datetime.now(), '%Y%m')
    cur_cycle = ''.join(['1', str(cur_month)[2:]])
    billing_cycles = son.query(BillingCycle).filter(
        BillingCycle.billing_cycle_id < cur_cycle,
        BillingCycle.billing_cycle_id >= MIN_BILLING_CYCLE,
    ).order_by(BillingCycle.billing_cycle_id.desc()).limit(LIMIT_MONTH).all()

    min_date = min(map(lambda e: e.cycle_begin_date, billing_cycles))
    max_date = max(map(lambda b: b.cycle_end_date, billing_cycles))

    packet_users = son.query(
        ARedPacketUser
    ).filter(
        ARedPacketUser.finish_flag == FINISH_FLAG_NORMAL,
        ARedPacketUser.wing_eff_date < max_date,
        ARedPacketUser.wing_exp_date >= min_date,
        ARedPacketUser.red_id.in_([100439718])
    ).all()

    p = pool.Pool(500)
    jobs = []

    for user in packet_users:
        jobs.append(p.spawn(process, user.red_id))

    gevent.joinall(jobs)
    return 'pool tasks finished'


if __name__ == '__main__':
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
