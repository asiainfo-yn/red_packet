# -*- coding: UTF-8 -*-
import hashlib
from xml.etree import ElementTree as ET
from tornado.httpclient import HTTPClient
from datetime import timedelta, datetime
from sqlalchemy.sql import select, and_, insert
from defines.variables import *
from defines.app_errors import *
from public_class.async_func import AsyncModule, auto_release
from public_modules.acct_item_owe import *
from public_modules.payment import *
from public_modules.bill import *
from public_modules.a_bill_owe import *
from xml_element import *
from errors import *
from modules import *

__author__ = 'ym'

ALIPAY_KEY = '123456'
ALIPAY_TRUST_STAFF = 7011

TRUST_STATE_10C = '10C'
TRUST_STATE_10R = '10R'
TRUST_STATE_10X = '10X'
TRUST_STATE_00X = '00X'

ALIPAY_CONSUME = '201'
ALIPAY_REFUND = '903'
ALIPAY_SUCCESS = 'POR-0000'


def call_alipay_intf(url, xml_obj):
    """
    调用支付宝代扣/退款接口
    :param url:
    :param xml_obj:
    :return:
    """
    ct_root = xml_obj.svc_cont.ct_root

    sin_str = ''.join([
        'reqplatform=%s&' % ct_root.reqplatform,
        'payplatform=%s&' % ct_root.payplatform,
        'reqpaytype=%s&' % ct_root.reqpaytype,
        'timestamp=%s&' % ct_root.timestamp,
        'reqno=%s&' % ct_root.reqno,
        'requser=%s&' % ct_root.requser,
        'reqnumtype=%s&' % ct_root.reqnumtype,
        'reqnum=%s&' % ct_root.reqnum,
        'areacode=%s&' % ct_root.areacode,
        'payamount=%s&' % ct_root.payamount,
        'key=%s' % ALIPAY_KEY,
    ])
    ct_root.sign = hashlib.md5(sin_str).hexdigest().upper()

    xml_str = ConvertXML(xml_obj).toxml()
    client = HTTPClient()
    response = client.fetch(url, method='POST', body=xml_str)
    xml_res = response.body

    if xml_res is None:
        raise MyException(AlipayIntfError())

    # 解析EOP返回数据
    parser = ET.XMLParser(target=ET.TreeBuilder(), encoding='utf-8')
    root = ET.fromstring(xml_res, parser=parser)
    svc = root.find('SvcCont')
    if svc is None or svc.text is None:
        raise MyException(XmlParseError())
    svc_text = svc.text.encode('utf-8')

    # 解析支付宝返回数据
    parser = ET.XMLParser(target=ET.TreeBuilder(), encoding='utf-8')
    rct_root = ET.fromstring(svc_text, parser=parser)

    sin_str = ''.join([
        'reqplatform=%s&' % rct_root.findtext('reqplatform'),
        'payplatform=%s&' % rct_root.findtext('payplatform'),
        'reqpaytype=%s&' % rct_root.findtext('reqpaytype'),
        'timestamp=%s&' % rct_root.findtext('timestamp'),
        'reqno=%s&' % rct_root.findtext('reqno'),
        'requser=%s&' % rct_root.findtext('requser'),
        'reqnumtype=%s&' % rct_root.findtext('reqnumtype'),
        'reqnum=%s&' % rct_root.findtext('reqnum'),
        'areacode=%s&' % rct_root.findtext('areacode'),
        'payamount=%s&' % rct_root.findtext('payamount'),
        'respcode=%s&' % rct_root.findtext('respcode'),
        'respmsg=%s&' % rct_root.findtext('respmsg').encode('utf-8'),
        'key=%s' % ALIPAY_KEY,
    ])
    m_sign = hashlib.md5(sin_str).hexdigest().upper()
    r_sign = rct_root.findtext('sign')
    if m_sign != r_sign:
        raise MyException(SignValidateError())

    return rct_root.findtext('respcode'), rct_root.findtext('respmsg').encode('utf-8')


def trust(son, acct_id):
    """
    托收-不做了，直接从支付宝代扣
    :param son:
    :param acct_id:
    :return:
    """
    result = VirSuccess()
    son_objects = list()
    try:
        # 锁ACCT表
        son.query(Acct).filter(
            Acct.acct_id == acct_id
        ).with_lockmode('update_nowait')

        # 查看是否欠费
        owe_state = son.query(AAcctOweState).filter(
            AAcctOweState.acct_id == acct_id,
            AAcctOweState.state == OWE_STATE_10A,
        ).all()
        if len(owe_state) == 0:
            raise MyException(OweInfoNotExist())

        # 查询该账户下是否都是后付费用户
        sv_num = son.query(func.count('*')).select_from(Serv).join(
            ServAcct, ServAcct.serv_id == Serv.serv_id
        ).filter(
            ~Serv.state.in_(['2HX', '2IX']),
            ServAcct.acct_id == acct_id,
            ServAcct.state == '10A',
            Serv.billing_mode_id.in_([2, 3])
        ).scalar()
        if sv_num > 0:
            raise MyException(PreChargeUserExist())

        for owe in owe_state:
            # 生成违约金记录，并插入临时表-暂时不做
            pass

            # 判断是否有托收费用-否则托收会和其他程序冲突
            key = str(200000 + int(owe.billing_cycle_id) - 10000)
            cls_owe = TB_ACCT_ITEM_OWE.get(key)
            jc_num = son.query(func.count('*')).filter(
                cls_owe.acct_id == acct_id,
                cls_owe.state == OWE_5JC,
            ).scalar()
            if jc_num > 0:
                raise MyException(OtherTrustRecordExist())

            # 计算欠费金额
            owe_charge = son.query(func.sum(cls_owe.amount)).filter(
                cls_owe.acct_id == acct_id,
                cls_owe.state == OWE_5JA,
            ).scalar()

            if owe_charge <= 0:
                raise MyException(TrustAmountIsZero())

            # 更新欠费状态表为10C
            owe_state.state = OWE_STATE_10C
            son_objects.append(owe_state)

            # 插入日志表-保存账户标识和金额，销账时要判断金额是否一致
            '''
            trust_log = AAgentTrustLog()
            trust_log.acct_id = acct_id
            trust_log.amount = owe_charge
            trust_log.billing_cycle_id = owe.billing_cycle_id
            trust_log.state = TRUST_STATE_10C
            son_objects.append(trust_log)
            '''

        result = Success()
        result.msg = '托收成功'
    except MyException, ex:
        # 处理结果插入结果表
        result = ex.value
    except Exception, ex:
        result = SystemExcept()
        result.msg = ex.message
    finally:
        try:
            if result.code != SystemExcept().code and len(son_objects) > 0:
                son.add_all(son_objects)
                son.commit()
            else:
                son.rollback()
        except Exception, ex2:
            result = SystemExcept()
            result.msg = ex2.message
            son.rollback()

    return result


def cash(son, acct_id, cycle_id, amount):
    """
    销账
    :param son:
    :param acct_id:
    :param cycle_id:
    :param amount:
    :return:
    """
    result = VirSuccess()
    son_objects = list()
    req_no = None
    payment_id = None
    try:
        cur_key = datetime.strftime(datetime.now(), '%Y%m')
        owe_key = str(200000 + int(cycle_id) - 10000)
        cur_cycle_id = int(cur_key) - 200000 + 10000
        # 锁ACCT表
        try:
            son.query(Acct).filter(
                Acct.acct_id == acct_id
            ).with_for_update(read=False, nowait=True).first()
        except Exception, ex:
            logging.error(ex.message)
            raise MyException(LockTableFailed())

        # 查询该账户下是否都是后付费用户
        sv_num = son.query(func.count('*')).select_from(Serv).join(
            ServAcct, ServAcct.serv_id == Serv.serv_id
        ).filter(
            ~Serv.state.in_(['2HX', '2IX']),
            ServAcct.acct_id == acct_id,
            ServAcct.state == '10A',
            Serv.billing_mode_id.in_([2, 3])
        ).scalar()
        if sv_num > 0:
            raise MyException(PreChargeUserExist())

        # 查看是否销账
        owe_state = son.query(AAcctOweState).filter(
            AAcctOweState.acct_id == acct_id,
            AAcctOweState.billing_cycle_id == cycle_id,
            AAcctOweState.state == OWE_STATE_10A,
        ).first()
        if owe_state is None:
            raise MyException(OweFeeNotTrust())

        # 比对销账金额和日志表中金额是否一致
        cls_owe = TB_ACCT_ITEM_OWE.get(owe_key)
        if cls_owe is None:
            raise MyException(GetOweTbFailed())
        owe_amount = son.query(func.nvl(func.sum(cls_owe.amount), 0)).filter(
            cls_owe.acct_id == acct_id,
            cls_owe.state == OWE_5JA,
        ).scalar()

        if owe_amount != amount:
            raise MyException(OweFeeNETrustFee())

        # 取代表号码
        deputy = son.query(AAcctDeputy).filter(
            AAcctDeputy.acct_id == acct_id,
        ).first()
        if deputy is None:
            raise MyException(DeputyNotExist())

        # 取序列
        payment_id = son.execute(select([Sequence('PAYMENT_ID_SEQ').next_value()])).scalar()
        bill_id = son.execute(select([Sequence('BILL_ID_SEQ').next_value()])).scalar()

        # 插入payment表
        cls_payment = TB_PAYMENT.get(cur_key)
        if cls_payment is None:
            raise MyException(GetPaymentTbFailed())
        payment = cls_payment()
        payment.payment_id = payment_id
        payment.acct_id = acct_id
        payment.payment_method = 11
        payment.payed_method = 14
        payment.operation_type = PAYMENT_OPER_5KA
        payment.amount = amount
        payment.state = PAYMENT_STATE_C0C
        payment.staff_id = ALIPAY_TRUST_STAFF
        payment.serv_id = deputy.serv_id
        payment.acc_nbr = deputy.acc_nbr
        payment.pay_cycle_id = cur_cycle_id
        son_objects.append(payment)

        # 插入bill表
        cls_bill = TB_BILL.get(cur_key)
        if cls_bill is None:
            raise MyException(GetBillTbFailed())
        bill = cls_bill()
        bill.bill_id = bill_id
        bill.payment_id = payment_id
        bill.payment_method = 11
        bill.billing_cycle_id = cur_cycle_id
        bill.acct_id = acct_id
        bill.serv_id = deputy.serv_id
        bill.acc_nbr = deputy.acc_nbr
        bill.bill_amount = amount
        bill.staff_id = ALIPAY_TRUST_STAFF
        bill.state = BILL_STATE_40C
        son_objects.append(bill)

        # 更新acct_item_owe表
        up_owe_num = son.query(cls_owe).filter(
            cls_owe.acct_id == acct_id,
            cls_owe.state == OWE_5JA,
        ).update({
            cls_owe.state: OWE_5JB,
            cls_owe.bill_id: bill_id,
            cls_owe.state_date: datetime.now(),
        })
        if up_owe_num == 0:
            raise MyException(UpdateNoneRecord())

        # 插入a_bill_owe表
        cls_bill_owe = TB_A_BILL_OWE.get(cur_key)
        if cls_bill_owe is None:
            raise MyException(GetBillOweTbFailed())
        o = son.query(
            cls_owe.acct_item_id,
            cls_owe.item_source_id,
            cls_owe.bill_id,
            cls_owe.acct_item_type_id,
            cls_owe.billing_cycle_id,
            cls_owe.acct_id,
            cls_owe.serv_id,
            cls_owe.amount,
            cls_owe.created_date,
            cls_owe.fee_cycle_id,
            cls_owe.payment_method,
            cls_owe.state,
            cls_owe.state_date,
            cls_owe.inv_offer,
            cls_owe.offer_id,
            cls_owe.ori_acct_item_id,
            cls_owe.invoice_id,
            cls_owe.corpus_flag,
        ).filter(
            cls_owe.acct_id == acct_id,
            cls_owe.bill_id == bill_id,
            cls_owe.state == OWE_5JB,
        )
        son.execute(insert(cls_bill_owe).from_select([
            cls_bill_owe.acct_item_id,
            cls_bill_owe.item_source_id,
            cls_bill_owe.bill_id,
            cls_bill_owe.acct_item_type_id,
            cls_bill_owe.billing_cycle_id,
            cls_bill_owe.acct_id,
            cls_bill_owe.serv_id,
            cls_bill_owe.amount,
            cls_bill_owe.created_date,
            cls_bill_owe.fee_cycle_id,
            cls_bill_owe.payment_method,
            cls_bill_owe.state,
            cls_bill_owe.state_date,
            cls_bill_owe.inv_offer,
            cls_bill_owe.offer_id,
            cls_bill_owe.ori_acct_item_id,
            cls_bill_owe.invoice_id,
            cls_bill_owe.corpus_flag,
        ], o))

        # 更新a_acct_owe_state表
        owe_state.state = OWE_STATE_10X
        owe_state.state_detail = OWE_5JB
        owe_state.state_date = func.now()
        son_objects.append(owe_state)

        # 插入a_modify_tax_api表
        modify = AModifyTaxApi()
        modify.acct_id = acct_id
        modify.payment_id = payment_id
        modify.bill_id = bill_id
        modify.modify_type = 0
        modify.act_flag = 'Y'
        modify.state = MODIFY_STATE_P0C
        son_objects.append(modify)

        # 拼接支付宝调用报文
        now = datetime.now()
        req_no = ''.join(['ALIPAY', now.strftime('%Y%m%d%H%M%S'), str(now.microsecond)])
        req_time = now.strftime('%Y%m%d%H%M%S')
        xml_obj = ContractRoot()
        tcp_cont = xml_obj.tcp_cont
        ct_root = xml_obj.svc_cont.ct_root

        tcp_cont.SrcTransactionNbr = req_no
        tcp_cont.ReqTime = req_time

        ct_root.timestamp = req_time
        ct_root.reqno = req_no
        ct_root.requser = str(acct_id)
        ct_root.payamount = str(amount)
        ct_root.reqpaytype = ALIPAY_CONSUME

        '''
        sin_str = ''.join([
            'reqplatform=%s&' % ct_root.reqplatform,
            'payplatform=%s&' % ct_root.payplatform,
            'reqpaytype=%s&' % ct_root.reqpaytype,
            'timestamp=%s&' % ct_root.timestamp,
            'reqno=%s&' % ct_root.reqno,
            'requser=%s&' % ct_root.requser,
            'reqnumtype=%s&' % ct_root.reqnumtype,
            'reqnum=%s&' % ct_root.reqnum,
            'areacode=%s&' % ct_root.areacode,
            'payamount=%s&' % ct_root.payamount,
            'key=%s' % ALIPAY_KEY,
        ])
        ct_root.sign = hashlib.md5(sin_str).hexdigest().upper()

        url = son.query(ABssOrgSwitch.switch_value).filter(
            ABssOrgSwitch.switch_id == EOP_ALIPAY_SWITCH_ID,
        ).scalar()

        xml_str = ConvertXML(xml_obj).toxml()
        client = HTTPClient()
        response = client.fetch(url, method='POST', body=xml_str)
        xml_res = response.body

        if xml_res is None:
            raise MyException(AlipayIntfError())

        # 解析EOP返回数据
        parser = ET.XMLParser(target=ET.TreeBuilder(), encoding='utf-8')
        root = ET.fromstring(xml_res, parser=parser)
        svc = root.find('SvcCont')
        if svc is None:
            raise MyException(XmlParseError())
        svc_text = svc.text.encode('utf-8')
        if svc_text is None:
            raise MyException(XmlParseError())

        # 解析支付宝返回数据
        parser = ET.XMLParser(target=ET.TreeBuilder(), encoding='utf-8')
        rct_root = ET.fromstring(svc_text, parser=parser)

        sin_str = ''.join([
            'reqplatform=%s&' % rct_root.findtext('reqplatform'),
            'payplatform=%s&' % rct_root.findtext('payplatform'),
            'reqpaytype=%s&' % rct_root.findtext('reqpaytype'),
            'timestamp=%s&' % rct_root.findtext('timestamp'),
            'reqno=%s&' % rct_root.findtext('reqno'),
            'requser=%s&' % rct_root.findtext('requser'),
            'reqnumtype=%s&' % rct_root.findtext('reqnumtype'),
            'reqnum=%s&' % rct_root.findtext('reqnum'),
            'areacode=%s&' % rct_root.findtext('areacode'),
            'payamount=%s&' % rct_root.findtext('payamount'),
            'respcode=%s&' % rct_root.findtext('respcode'),
            'respmsg=%s&' % rct_root.findtext('respmsg').encode('utf-8'),
            'key=123456',
        ])
        m_sign = hashlib.md5(sin_str).hexdigest().upper()
        r_sign = rct_root.findtext('sign')
        if m_sign != r_sign:
            raise MyException(SignValidateError())
        '''

        # 调用支付宝代扣接口
        url = son.query(ABssOrgSwitch.switch_value).filter(
            ABssOrgSwitch.switch_id == EOP_ALIPAY_SWITCH_ID,
        ).scalar()
        agent_code, agent_msg = call_alipay_intf(url, xml_obj)

        result = Success()
        result.agent = agent_code
        result.msg = agent_msg
        raise MyException(result)
    except MyException, ex:
        result = ex.value
    except Exception, ex:
        result = SystemExcept()
        result.msg = ex.message
    finally:
        try:
            if result.code == Success().code \
                    and result.agent == ALIPAY_SUCCESS \
                    and len(son_objects) > 0:
                son.add_all(son_objects)
                son.commit()
            else:
                son.rollback()
        except Exception, ex2:
            son.rollback()
            result = SystemExcept()
            result.msg = ex2.message
        finally:
            # 写入日志表
            trust_log = AAgentTrustLog()
            trust_log.acct_id = acct_id
            trust_log.payment_id = payment_id
            trust_log.amount = amount
            trust_log.billing_cycle_id = cycle_id
            trust_log.state = TRUST_STATE_10C
            trust_log.oper_type = ALIPAY_CONSUME
            trust_log.bill_result = result.code
            trust_log.pay_result = result.agent
            trust_log.request_no = req_no
            son.add(trust_log)
            son.commit()

    return result


def reverse(son, acct_id):
    """
    返销
    :param son:
    :param acct_id:
    :return:
    """
    result = VirSuccess()
    son_objects = list()
    try:
        # 锁ACCT表
        son.query(Acct).filter(
            Acct.acct_id == acct_id
        ).with_lockmode('update_nowait')
    except Exception, ex:
        result = SystemExcept()
        result.msg = ex.message
    finally:
        try:
            if result.code != SystemExcept().code and len(son_objects) > 0:
                son.add_all(son_objects)
                son.commit()
        except Exception, ex2:
            result = SystemExcept()
            result.msg = ex2.message
            son.rollback()

    return result


class AsyncTrustAlipay(object):
    def __init__(self):
        self.async = AsyncModule()

    @auto_release
    def process_trust(self, args):
        result = Success()
        son = self.async.session
        acct_id = int(args.get('acct_id'))

        try:
            result = trust(son, acct_id)
        except Exception as ex:
            result = SystemExcept()
            result.msg = ex.message
        finally:
            if result is None:
                result = UnknownError()
                result.msg = 'result is None'

        return result.to_json()

    @auto_release
    def process_cash_bill(self, args):
        result = Success()
        son = self.async.session
        acct_id = int(args.get('acct_id'))
        cycle_id = int(args.get('billing_cycle_id'))
        amount = int(args.get('amount'))

        try:
            result = cash(son, acct_id, cycle_id, amount)
        except Exception as ex:
            result = SystemExcept()
            result.msg = ex.message
        finally:
            if result is None:
                result = UnknownError()
                result.msg = 'result is None'

        return result.to_json()

    @auto_release
    def process_reverse_bill(self, args):
        result = Success()
        son = self.async.session
        acct_id = args.get('acct_id')

        try:
            result = reverse(son, acct_id)
        except Exception as ex:
            result = SystemExcept()
            result.msg = ex.message
        finally:
            if result is None:
                result = UnknownError()
                result.msg = 'result is None'

        return result.to_json()
