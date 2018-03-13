# -*- coding: UTF-8 -*-
from os import environ
from dict4ini import *
from datetime import *
from time import sleep
import logging
import xml.etree.ElementTree
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from services.red_packet.modules import *
from public_class.convert_xml import Basic, ConvertXML
import urllib
import urllib2

# url_header = 'http://135.33.10.41:8301/acct/alipay/consume'
url_header = 'http://135.33.9.231:8005/acct/alipay/consume'

packet_name = 'alipay_bill'
FORMAT = '%(asctime)s %(process)d %(name)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO, filename=''.join([packet_name, '.log']))
logger = logging.getLogger(packet_name)

SUCCESS = '0'
STATE_OPEN = 'OPEN'
STATE_CLOSE = 'CLOSE'
STATE_ERROR = 'ERROR'
STAFF_ID = 7010
BALANCE_TYPE_ID = 2


class AAlipayLifeCycle(Base):
    __tablename__ = 'a_alipay_lifecycle'

    nslc_id = Column(Integer, primary_key=True)
    acct_id = Column(Integer)
    serv_id = Column(Integer)
    area_code = Column(Integer)
    pay_fee = Column(Integer)
    acc_nbr = Column(String(32))
    state = Column(String(6))
    state_date = Column(DateTime)


class AAgentPayLog(Base):
    __tablename__ = 'a_agent_pay_log'

    nslc_id = Column(Integer, primary_key=True)
    payment_id = Column(Integer)
    request_no = Column(String(32))
    bill_result = Column(String(16))
    pay_result = Column(String(16))
    create_date = Column(DateTime)
    oper_type = Column(Integer)
    amount = Column(Integer)
    pay_plat_form = Column(String(8))


class RequestRoot(Basic):
    __name__ = 'RequestRoot'

    def __init__(self):
        self.NSLC_ID = None
        self.ACC_NBR = None
        self.AREA_CODE = None
        self.STAFF_ID = None
        self.REQUEST_NO = None
        self.BALANCE_TYPE_ID = None
        self.ACCT_ITEM_GRUP_ID = None
        self.PAYMENT_CHARGE = None
        self.EFF_DATE = None
        self.EXP_DATE = None
        self.CYCLE_UPPER = None
        self.SOURCE_DESC = 'alipay deposit'


def process(pay):
    global son

    r = RequestRoot()
    r.NSLC_ID = pay.nslc_id
    r.ACC_NBR = pay.acc_nbr
    r.AREA_CODE = ''.join(['0', str(pay.area_code)])
    r.STAFF_ID = STAFF_ID
    r.BALANCE_TYPE_ID = BALANCE_TYPE_ID
    r.PAYMENT_CHARGE = pay.pay_fee

    converter = ConvertXML(r)
    request_content = converter.toxml().encode('utf-8')
    url = url_header

    req = urllib2.Request(url, data=request_content)
    response = urllib2.urlopen(req)
    res = response.read()
    res = res.decode('gbk').encode('utf-8')

    content = xml.etree.ElementTree.fromstring(res)
    result = content.findtext('Result')
    remark = content.findtext('ResultMark')
    req_no = content.findtext('REQUEST_NO')
    pay_id = content.findtext('PAYMENT_ID')

    logging.info(','.join([result, remark, req_no, pay_id]))

    log_num = son.query(func.count('*')).filter(
        AAgentPayLog.nslc_id == pay.nslc_id,
        AAgentPayLog.oper_type == 0,
        AAgentPayLog.bill_result == SUCCESS
    ).scalar()
    if log_num > 0 and result == SUCCESS:
        pay.state = STATE_CLOSE
    else:
        pay.state = STATE_ERROR

    son.add(pay)
    son.commit()


def start():
    global son
    result = True

    try:
        # 查询所有处于开启状态的数据
        pay_data = son.query(AAlipayLifeCycle).filter(
            AAlipayLifeCycle.state == STATE_OPEN,
        ).all()

        logger.info('len(packet_dict)=%d' % len(pay_data))

        for pay in pay_data:
            process(pay)
    except Exception, ex:
        result = False
        logger.error(ex.message)

    return result


if __name__ == '__main__':
    """
    预付费用户支付宝代扣程序
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
    
    while True:
        if start():
            sleep(10)
        else:
            break
    son.close()
