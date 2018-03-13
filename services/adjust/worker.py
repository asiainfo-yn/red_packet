# -*- coding: UTF-8 -*-
import hashlib
import cx_Oracle
from xml.etree import ElementTree as ET
from tornado.httpclient import HTTPClient
from datetime import timedelta, datetime
from sqlalchemy.sql import select, and_, insert
from defines.variables import *
from defines.app_errors import *
from public_class.async_func import AsyncModule, auto_release
from public_class.interface import call_cash_bill_intf
from public_modules.models import *
from errors import *
from xml_element import *


FORE_ADJUST = '2'
ACTION_TYPE = '-1'
VALUE_TYPE = '0'
AUTO_CHECK = '1'
SRC_CONTENT = ''
DUTY_PART = '2'
TO_BALANCE = '1'
OBJECT_TYPE_ID = '1'
ITEM_GROUP_ID = ''
ADJUST_URL = 'http://135.33.9.231:8005/acct/adjust/deposit'
REVERSE_URL = 'http://135.33.9.231:8005/acct/adjust/reverse'


class AdjustResult(Basic):
    __name__ = 'AdjustResult'

    def __init__(self):
        self.PaymentId = None
        self.NslcId = None


def adjust_bt(son, args):
    result = VirSuccess()
    son_objects = list()
    # cursor = son.connection().engine.raw_connection().cursor()

    try:
        serv_id = son.query(Serv.serv_id).filter(
            Serv.acc_nbr == args.get('AccNbr'),
            ~Serv.state.in_(['2IX', '2HX'])
        ).scalar()

        if serv_id is None:
            raise MyException(UserOffLine())

        acct_id = son.query(ServAcct.acct_id).filter(
            ServAcct.serv_id == serv_id,
            ServAcct.state == '10A',
        ).order_by(ServAcct.state_date.desc()).scalar()

        if acct_id is None:
            raise MyException(GetAcctIdFailed())

        audit_id = son.execute(select([Sequence('seq_charge_adjust_audit_log').next_value()])).scalar()
        log_id = son.execute(select([Sequence('seq_charge_adjust_log_id').next_value()])).scalar()

        src_content = ''
        adjust_content = ''
        amount = 0
        for item in args.get('AdjustContent'):
            '''
            s_cont = ','.join([item.get('ItemTypeId'), item.get('Amount'), '', '', str(acct_id)])
            a_cont = ','.join([item.get('ItemTypeId'), item.get('Amount'), '', '', str(acct_id)])
            src_content = ''.join([src_content, s_cont, '|'])
            adjust_content = ''.join([adjust_content, a_cont, '|'])
            '''
            charge = float(item.get('Amount'))
            item_type_id = int(item.get('ItemTypeId'))
            amount -= charge * 100

            adj_dtl = AcctItemAdjustDetail()
            adj_dtl.adjust_audit_log_id = audit_id
            adj_dtl.acct_item_type_id = item_type_id
            adj_dtl.amount = charge
            adj_dtl.acct_item_adjust_type_id = item_type_id
            adj_dtl.charge = charge
            adj_dtl.serv_id = serv_id
            adj_dtl.acct_id = acct_id
            son_objects.append(adj_dtl)

        amount = int(amount)

        if amount == 0:
            raise MyException(AdjustAmountIsZero())

        """
        src_content = src_content[:-1]
        adjust_content = adjust_content[:-1]

        o_acct_id = cursor.var(cx_Oracle.STRING)
        o_audit_log_id = cursor.var(cx_Oracle.STRING)
        o_balance_sync_id = cursor.var(cx_Oracle.STRING)
        o_result = cursor.var(cx_Oracle.NUMBER)
        o_info = cursor.var(cx_Oracle.STRING)

        proc_args = [
            args.get('StaffId'),
            str(serv_id),
            FORE_ADJUST,
            args.get('BillingCycleId'),
            args.get('Reason'),
            args.get('ReasonAppend'),
            ACTION_TYPE,
            VALUE_TYPE,
            AUTO_CHECK,
            src_content,
            adjust_content,
            DUTY_PART,
            TO_BALANCE,
            OBJECT_TYPE_ID,
            ITEM_GROUP_ID,
            o_acct_id, o_audit_log_id, o_balance_sync_id, o_result, o_info
        ]

        cursor.callproc("PKG_CHARGE_ADJUST.P_ADJUST_CALL", proc_args)

        o_code = int(o_result.getvalue())
        o_msg = o_info.getvalue().decode('gbk')

        logging.info('procedure:code=%s,msg=%s' % (str(o_code), o_msg))
        """
        # 获取当前月份账期
        month = datetime.strftime(datetime.now(), '%Y%m')
        cycle_id = int(month) - 200000 + 10000

        audit = AChargeAdjustAudit()
        audit.adjust_audit_log_id = audit_id
        audit.acct_id = acct_id
        audit.serv_id = serv_id
        audit.acct_item_type_id = 0
        audit.adjust_acct_item_type_id = 102
        audit.adjust_type = 3
        audit.adjust_value = -amount
        audit.billing_cycle_id = args.get('BillingCycleId')
        audit.apply_staff_id = args.get('StaffId')
        audit.audit_staff_id = args.get('StaffId')
        audit.audit_reason = u'转余额自动审核'.encode('gbk')
        audit.state = 'A0P'
        audit.adjust_apply_flag = 1
        audit.is_fore_adjust = 'T'
        audit.adjust_billing_cycle_id = cycle_id
        audit.duty_org_id = 2
        audit.adjust_reason = args.get('Reason')
        audit.adjust_reason_append = args.get('ReasonAppend')
        audit.object_type_id = 1

        adj_log = AChargeAdjustLog()
        adj_log.adjust_log_id = log_id
        adj_log.acct_id = acct_id
        adj_log.serv_id = serv_id
        adj_log.acct_item_type_id = 0
        adj_log.adjust_type = 3
        adj_log.adjust_charge = -amount
        adj_log.billing_cycle_id = args.get('BillingCycleId')
        adj_log.staff_id = args.get('StaffId')
        adj_log.adjust_audit_log_id = audit_id
        adj_log.state = 'A0P'
        adj_log.is_fore_adjust = 'T'
        adj_log.adjust_reason = args.get('Reason')

        # if int(o_code) in (10, 20):
        # 存过返回成功，调用预存接口
        nslc_id = son.execute(select([Sequence('seq_nslc_id').next_value()])).scalar()
        xml_obj = RequestCashRoot()
        xml_obj.NSLC_ID = nslc_id
        xml_obj.ACC_NBR = args.get('AccNbr')
        xml_obj.STAFF_ID = args.get('StaffId')
        xml_obj.BALANCE_TYPE_ID = 4
        xml_obj.PAYMENT_CHARGE = amount
        xml_obj.SOURCE_DESC = u'调帐转预存'.encode('gbk')

        code, msg, pay, nslc = call_cash_bill_intf(ADJUST_URL, xml_obj)

        if code == '0':
            # acct_item_id赋值为payment_id，以后通过该字段查询调账日志
            adj_log.acct_item_id = pay
            son_objects.append(audit)
            son_objects.append(adj_log)

            adj_res = AdjustResult()
            adj_res.PaymentId = pay
            adj_res.NslcId = nslc

            result = Success()
            result.items = adj_res
        else:
            e = AdjustInterfaceError()
            e.msg = '-'.join([code, msg])
            raise MyException(e)
        # else:
        #     raise MyException(CallProcedureError())

    except MyException as ex:
        result = ex.value
    except Exception as ex:
        result = SystemExcept()
        result.msg = ex.message
    finally:
        try:
            # cursor.close()
            if result.code == Success().code and len(son_objects) > 0:
                son.add_all(son_objects)
                son.commit()
            else:
                son.rollback()
        except Exception as ex2:
            son.rollback()
            result = SystemExcept()
            result.msg = ex2.message

    return result


def adjust_bt_reverse(son, args):
    """
    调账返销
    :param son: 数据库连接实例
    :param args: xml参数
    :return:
    """
    result = VirSuccess()
    son_objects = list()

    try:
        nslc_id = args.get('NslcId')
        staff_id = args.get('StaffId')
        amount = args.get('Amount')
        # 取payment_id
        payment_id = son.query(AAgentPayLog.payment_id).filter(
            AAgentPayLog.nslc_id == nslc_id
        ).scalar()
        if payment_id is None:
            raise Exception(AdjustNslcNotFound())

        # 取调账日志
        adj_log_id = son.query(AChargeAdjustLog.adjust_log_id).filter(
            AChargeAdjustLog.acct_item_id == payment_id
        ).scalar()
        if adj_log_id is None:
            raise Exception(AdjustLogNotFound())

        # 拼装xml报文，并调用计费返销接口
        xml_obj = RequestReverseRoot()
        xml_obj.NSLC_ID = nslc_id
        xml_obj.STAFF_ID = staff_id
        xml_obj.PAYMENT_CHARGE = amount

        code, msg, pay, nslc = call_cash_bill_intf(REVERSE_URL, xml_obj)

        if code == '0':
            # acct_item_id赋值为payment_id，以后通过该字段查询调账日志
            son.query.filter(
                AChargeAdjustAudit.adjust_audit_log_id == adj_log_id
            ).update({AChargeAdjustAudit.state: ''})

            son.query.filter(
                AChargeAdjustLog.adjust_log_id == adj_log_id
            ).update({AChargeAdjustLog.state: ''})

            result = Success()
        else:
            e = AdjustInterfaceError()
            e.msg = '-'.join([code, msg])
            raise MyException(e)
    except MyException as ex:
        result = ex.value
    except Exception as ex:
        result = SystemExcept()
        result.msg = ex.message
    finally:
        try:
            if result.code == Success().code and len(son_objects) > 0:
                son.add_all(son_objects)
                son.commit()
            else:
                son.rollback()
        except Exception as ex2:
            son.rollback()
            result = SystemExcept()
            result.msg = ex2.message

    return result


class Adjust(object):
    def __init__(self):
        self.async = AsyncModule()

    @auto_release
    def deposit(self, param):
        """调账-补退"""
        result = Success()
        son = self.async.session

        try:
            try:
                # param = param.decode('gbk').encode('utf-8')
                parser = ET.XMLParser(target=ET.TreeBuilder(), encoding='utf-8')
                root = ET.fromstring(param, parser=parser)
            except Exception as ex:
                raise MyException(XmlParseError())

            staff_id = root.findtext('StaffId')
            acc_nbr = root.findtext('AccNbr')
            cycle_id = root.findtext('BillingCycleId')
            reason = root.findtext('Reason')
            append = root.findtext('ReasonAppend')
            content = root.find('AdjustContent')

            if staff_id is None or acc_nbr is None or cycle_id is None \
                    or reason is None or append is None or content is None:
                raise MyException(XmlParseError())

            items = []
            for c in content:
                item_id = c.findtext('ItemTypeId')
                amount = c.findtext('Amount')

                if item_id is None or amount is None:
                    raise MyException(XmlParseError())

                items.append({'ItemTypeId': item_id, 'Amount': amount})

            if len(items) == 0:
                raise MyException(XmlParseError())

            args = {
                'StaffId': str(staff_id),
                'AccNbr': str(acc_nbr),
                'BillingCycleId': str(cycle_id),
                'Reason': reason,
                'ReasonAppend': append,
                'AdjustContent': items
            }

            result = adjust_bt(son, args)
        except Exception as ex:
            result = SystemExcept()
            result.msg = ex.message
        finally:
            if result is None:
                result = UnknownError()
                result.msg = 'result is None'

        return result.to_xml()

    @auto_release
    def gather(self, param):
        """调账-补收"""
        pass

    @auto_release
    def reverse(self, param):
        """调账-补退-返销"""
        result = Success()
        son = self.async.session

        try:
            try:
                parser = ET.XMLParser(target=ET.TreeBuilder(), encoding='utf-8')
                root = ET.fromstring(param, parser=parser)
            except Exception as ex:
                raise MyException(XmlParseError())

            staff_id = root.findtext('StaffId')
            nslc_id = root.findtext('NslcId')
            amount = root.findtext('Amount')

            if staff_id is None or nslc_id is None or amount is None:
                raise MyException(XmlParseError())

            args = {
                'StaffId': str(staff_id),
                'NslcId': str(nslc_id),
                'Amount': str(amount),
            }

            result = adjust_bt_reverse(son, args)
        except Exception as ex:
            result = SystemExcept()
            result.msg = ex.message
        finally:
            if result is None:
                result = UnknownError()
                result.msg = 'result is None'

        return result.to_xml()


if __name__ == '__main__':
    args = """
    <RequestRoot>
        <StaffId>82383</StaffId>
        <AccNbr>18087553521</AccNbr>
        <BillingCycleId>11712</BillingCycleId>
        <Reason>test</Reason>
        <ReasonAppend>ym</ReasonAppend>
        <AdjustContent>
            <AdjustItem>
                <ItemTypeId>610</ItemTypeId>
                <Amount>-0.03</Amount>
            </AdjustItem>
            <AdjustItem>
                <ItemTypeId>611</ItemTypeId>
                <Amount>-0.01</Amount>
            </AdjustItem>
        </AdjustContent>
    </RequestRoot>
    """
    a = Adjust()
    print(a.deposit(args))
