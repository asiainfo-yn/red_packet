# -*- coding: UTF-8 -*-
from os import environ
from time import sleep
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


url_header = 'http://135.32.8.70/acct/red-packet/user/'

packet_name = 'packet_fc'
FORMAT = '%(asctime)s %(process)d %(name)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, filename=''.join([packet_name, '.log']))
logger = logging.getLogger(packet_name)
billing_cycles = None
g_len = 0
sum_users = 0


def process(red_id):
    """
    分成只对上个月数据处理
    :param red_id:
    :return:
    """
    global billing_cycles, g_len, sum_users

    try:
        packets = map(lambda b: dict(
            red_id=red_id, acct_month=b.cycle_begin_date.strftime('%Y%m')
        ), billing_cycles)

        packets = sorted(packets, key=lambda m: m.get('acct_month'))
        for packet in packets:
            acct_month = packet.get('acct_month')

            url = ''.join([url_header, str(red_id)])
            request_content = dict(month=acct_month, action_type=ACTION_TYPE_FC)

            req = urllib2.Request(url, data=urllib.urlencode(request_content))
            response = urllib2.urlopen(req)
            res = ujson.loads(response.read())

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
            logger.info('processed %d, left %d' % (g_len, sum_users))


def start():
    global son, billing_cycles, sum_users

    # 取前三个月账期
    cur_month = datetime.strftime(datetime.now(), '%Y%m')
    cur_cycle = ''.join(['1', str(cur_month)[2:]])
    billing_cycles = son.query(BillingCycle).filter(
        BillingCycle.billing_cycle_id < cur_cycle,
        BillingCycle.billing_cycle_id >= MIN_BILLING_CYCLE,
    ).order_by(BillingCycle.billing_cycle_id.desc()).limit(1).all()

    min_date = min(map(lambda e: e.cycle_begin_date, billing_cycles))
    max_date = max(map(lambda b: b.cycle_end_date, billing_cycles))
    max_cycle_id = max(map(lambda c: c.billing_cycle_id, billing_cycles))

    # 检查同义词是否存在
    synonym_name = ''.join(['ACCT_ITEM_AGGR_', str(max_cycle_id), '%_HB'])
    aggr_num = son.query(func.count('*')).select_from(UserObjects).filter(
        UserObjects.object_name.like(synonym_name),
        UserObjects.object_type == 'SYNONYM',
    ).scalar()
    if aggr_num != 16:
        logging.error('ACCT_T5数据库总账表同义词数量不等于16，请核查后在重新运行')
        return False

    logging.info('开始读取需要分成的用户')
    packet_users = son.query(ARedPacketUser).filter(
        ARedPacketUser.finish_flag == FINISH_FLAG_NORMAL,
        ARedPacketUser.wing_eff_date < max_date,
        ARedPacketUser.wing_exp_date >= min_date,
    ).all()

    sum_users = len(packet_users)
    logging.info('读取到 %d 记录，开始分成' % sum_users)
    sleep(3)

    p = pool.Pool(500)
    jobs = []

    for user in packet_users:
        jobs.append(p.spawn(process, user.red_id))

    gevent.joinall(jobs)
    return 'fc program finished successfully'


if __name__ == '__main__':
    """分成客户端"""
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
