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


url_header = 'http://135.32.8.70/acct/red-packet/user/'

packet_name = 'packet_add'
FORMAT = '%(asctime)s %(process)d %(name)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, filename=''.join([packet_name, '.log']))
logger = logging.getLogger(packet_name)
g_len = 0


def process(packet):
    global g_len
    red_id = packet.get('red_id')
    acct_month = packet.get('acct_month')

    try:
        url = ''.join([url_header, str(red_id)])
        request_content = dict(month=acct_month, action_type=ACTION_TYPE_ADD)

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
    global son

    try:
        # 取前三个月账期
        cur_month = datetime.strftime(datetime.now(), '%Y%m')
        cur_cycle = ''.join(['1', str(cur_month)[2:]])
        billing_cycles = son.query(BillingCycle).filter(
            BillingCycle.billing_cycle_id < cur_cycle,
            BillingCycle.billing_cycle_id >= MIN_BILLING_CYCLE
        ).order_by(BillingCycle.billing_cycle_id.desc()).limit(LIMIT_MONTH).all()

        min_date = datetime.now()
        for c in billing_cycles:
            min_date = min(min_date, c.cycle_begin_date)

        min_month = min_date.strftime('%Y%m')

        # 查询欠费用户并补送
        packet_dict = dict()
        packet_user = son.query(ARedPacketUser).filter(
            ARedPacketUser.red_id == ARedPacket.red_id,
            ARedPacketUser.finish_flag == FINISH_FLAG_NORMAL
        )
        pk_owe = son.query(ARedPacket.red_id, ARedPacket.acct_month).filter(
            packet_user.exists(),
            ARedPacket.state == STATE_P0C,
        ).all()

        for pk in pk_owe:
            if packet_dict.get(pk.red_id) is None:
                packet_dict[pk.red_id] = [pk.acct_month]
            else:
                packet_dict[pk.red_id].append(pk.acct_month)

        logger.info('len(packet_dict)=%d' % len(packet_dict))

        packet_list = list()
        for pk, pv in packet_dict.iteritems():
            # 判断用户欠费是否大于3个月，大于则更新成永不赠送
            if len(pv) > LIMIT_MONTH:
                son.query(ARedPacketUser).filter(
                    ARedPacketUser.red_id == pk,
                    ARedPacketUser.finish_flag == FINISH_FLAG_NORMAL
                ).update({ARedPacketUser.finish_flag: FINISH_FLAG_OWE3MONTH})
                son.commit()
                logger.info('red_id=%d finished' % pk)
            else:
                # 判断欠费月份是否超过三个月，超过则不赠送（单账期欠费只给用户三个月交费时间）
                # 这里一般用于判断最后几个月的情况，比如用户套餐已经失效了，但是用户还有欠费，仍然要补送
                for m in pv:
                    if m >= min_month:
                        packet_list.append(dict(red_id=pk, acct_month=m))

        logger.info('len(packet_list)=%d' % len(packet_list))

        p = pool.Pool(500)
        jobs = []

        for packet in packet_list:
            jobs.append(p.spawn(process, packet))

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
