# -*- coding: UTF-8 -*-
from os import environ
import json
from dict4ini import *
from datetime import *
from time import sleep, strftime
import sqlalchemy
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.sql import select

import base64
from Crypto.Hash import SHA512
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from services.red_packet.modules import *
from CURLClient import CURLClient
import logging


__author__ = 'ym'
# 测试
# url = 'http://132.129.39.13:10080/mapi/businessStatusSynchronize'
# 正式
url = 'http://132.224.23.9:7007/mapi/businessStatusSynchronize'
key_file_name = 'redbag.pem'

packet_name = 'upload_real'
FORMAT = '%(asctime)s %(process)d %(name)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, filename=''.join([packet_name, '.log']))
logger = logging.getLogger(packet_name)


class Singleton(object):
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls)
        return cls._instance


class PrivateKey(Singleton):
    def __init__(self):
        if not hasattr(self, 'key'):
            self.key = None

        if self.key is None:
            with open(key_file_name) as f:
                self.key = f.read()

    def get_key(self):
        return self.key


def dealrealtime(s, red_type):
    result = False
    # 单个用户上传
    if s.upload_flag == 2:
        # 对于退订工单，先判断有没有订购记录，如果没有先上传订购再传退订
        up_count = son.query(func.count('*')).filter(
            ARedPacketUpload.red_id == s.seq_wing,
            ARedPacketUpload.upload_flag == 0
        ).scalar()
        if up_count == 0:
            # 递归调用，先把上传标识改成订购，上传成功后再改成退订
            s.upload_flag = 0
            if dealrealtime(s, red_type):
                s.upload_flag = 2
            else:
                # 上传订购报错，直接返回，不再对退订上传
                return False
    # 取用户设备号
    acc_nbr = son.query(Serv.acc_nbr).filter(
        Serv.serv_id == s.serv_id
    ).scalar()


    # 取用户赠送规则
    rule = son.query(ProductOfferInstance.product_offer_id).filter(
        ProductOfferInstance.product_offer_instance_id == s.product_offer_instance_id
    ).first()


    # 取流水序列
    seq_no = son.execute(select([Sequence('seq_red_packet_up_id').next_value()])).scalar()
    now = datetime.now()

    body = {
        'supplyOrgCode': '002530000000000',
        'publicKeyNum': '0',
        'productNo': acc_nbr,
        'promptCode': str(rule.product_offer_id),
        'operate': '01' if s.upload_flag == 0 else '02',
        'acceptOrgCode': '002530000000000',
        'acceptChannel': '',
        'acceptSeqNo': ''.join(['RB530', now.strftime('%Y%m%d%H%M%S'), str(now.microsecond)[:3], '%010d' % seq_no]),
        'inputTime': now.strftime('%Y-%m-%d %H:%M:%S'),
        'inputUId': '36',
        'protocolVersion': '1.0',
        'protocolBeginAt': '',
        'protocolEndAt': '',
        'rebateCycle': '',
        'firstRebateAt': ''
    }
    body_keys = body.keys()
    body_keys.sort()
    sin_str = ''

    for key in body_keys:
        sin_str = ''.join([sin_str, key, '=', body.get(key), '&'])

    sin_str = sin_str[:-1]

    # SHA512签名
    pri_key = PrivateKey().get_key()
    key = RSA.importKey(pri_key)
    signer = PKCS1_v1_5.new(key)
    h = SHA512.new(sin_str)
    signature = signer.sign(h)
    body['sign'] = base64.b64encode(signature)

    resp_str = json.dumps(body, ensure_ascii=False).encode('utf-8')
    # p_log.INFO(resp_str)

    head = [
        'Accept-Encoding: gzip,deflate',
        'Content-Type: application/json; charset=utf-8',
        'Content-Length: %d' % len(resp_str),
        'Connection: Keep-Alive',
    ]

    c = CURLClient(url)
    resp = c.request_post(head, resp_str)
    resp_json = json.loads(resp)

    up1 = ARedPacketUpload()
    up1.red_id = s.seq_wing
    up1.req_xml = resp_str
    up1.red_type = red_type

    if s.upload_flag == 0:
        up1.upload_flag = 0
    elif s.upload_flag == 2:
        up1.upload_flag = 2

    if resp_json.get('success'):
        result = True
        up1.remark = 'success'
        logger.info('serv_id=%s success' % s.serv_id)
    else:
        result = False
        up1.remark = 'err_code=%s,err_msg=%s' % (resp_json.get('errorCode'), resp_json.get('errorMsg'))
        logger.error('serv_id=%d failed,err_code=%s,err_msg=%s' %
                    (s.serv_id, resp_json.get('errorCode').encode('utf-8'), resp_json.get('errorMsg').encode('utf-8')))

    son.add(up1)
    son.commit()

    return result


def process():
    while True:
        # 取所有需要上传的数据
        try:
            # 预存红包数据上传
            up1 = son.query(ARedPacketUpload.red_id).filter(
                ARedPacketUpload.red_id == ProductOfferInstanceWing.seq_wing,
                ARedPacketUpload.upload_flag == ProductOfferInstanceWing.upload_flag
            )
            realtimeusers = son.query(ProductOfferInstanceWing).filter(
                ~up1.exists(),
                ProductOfferInstanceWing.upload_flag.isnot(None)
            ).limit(100).all()

            for realtimeuser in realtimeusers:
                dealrealtime(realtimeuser, 2)
        except Exception as ex:
            logger.error(ex.message)
            son.rollback()
        finally:
            sleep(10)


if __name__ == '__main__':
    global son
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

    process()
    son.close()
