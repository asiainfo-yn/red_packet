# -*- coding:utf8 -*-
import ujson
from public_class.convert_xml import Basic, ConvertXML

__author__ = 'yangming'


class RequestRoot(Basic):
    __name__ = 'RequestRoot'

    def __init__(self):
        self.ResultCode = None
        self.ResultMsg = None
        self.ResultItems = None


class MyException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ErrorCode(object):
    def __init__(self):
        self.result_code = 0
        self.agent_code = 0
        self.result_msg = ''
        self.result_items = None

    @property
    def code(self):
        return self.result_code

    @property
    def agent(self):
        return self.agent_code

    @agent.setter
    def agent(self, coding):
        self.agent_code = coding

    @property
    def msg(self):
        return self.result_msg

    @msg.setter
    def msg(self, message):
        self.result_msg = message

    @property
    def items(self):
        return self.result_items

    @items.setter
    def items(self, items):
        self.result_items = items

    def to_json(self):
        return ujson.dumps({'RESULT_CODE': self.code, 'RESULT_MSG': self.msg}, ensure_ascii=False)

    def to_xml(self):
        r = RequestRoot()
        r.ResultCode = self.code
        r.ResultMsg = self.msg
        r.ResultItems = self.items
        return ConvertXML(r).toxml()


class UnknownError(ErrorCode):
    def __init__(self):
        super(UnknownError, self).__init__()
        self.result_code = -1
        self.result_msg = '未知错误'


class Success(ErrorCode):
    def __init__(self):
        super(Success, self).__init__()
        self.result_code = 0
        self.result_msg = '处理成功'


class VirSuccess(ErrorCode):
    def __init__(self):
        super(VirSuccess, self).__init__()
        self.result_code = 1
        self.result_msg = '虚拟成功'


class ParameterNone(ErrorCode):
    def __init__(self):
        super(ParameterNone, self).__init__()
        self.result_code = 80001000
        self.result_msg = '传入参数为空'


class SystemExcept(ErrorCode):
    def __init__(self):
        super(SystemExcept, self).__init__()
        self.result_code = 90000000
        self.result_msg = '系统内部错误'


class GetAcctIdFailed(ErrorCode):
    def __init__(self):
        super(GetAcctIdFailed, self).__init__()
        self.result_code = 10002000
        self.result_msg = '取账户标识失败'


class UserOffLine(ErrorCode):
    def __init__(self):
        super(UserOffLine, self).__init__()
        self.result_code = 10002001
        self.result_msg = '用户已拆机'


class GetOweTbFailed(ErrorCode):
    def __init__(self):
        super(GetOweTbFailed, self).__init__()
        self.result_code = 10002001
        self.result_msg = '取OWE表出错'


class MonthInvalid(ErrorCode):
    def __init__(self):
        super(MonthInvalid, self).__init__()
        self.result_code = 10002002
        self.result_msg = '传入月份无效'


class DBConnectNotFound(ErrorCode):
    def __init__(self):
        super(DBConnectNotFound, self).__init__()
        self.result_code = 10002003
        self.result_msg = '数据库连接未找到'


class DataNotFound(ErrorCode):
    def __init__(self):
        super(DataNotFound, self).__init__()
        self.result_code = 10002004
        self.result_msg = '未查询到数据'


class GetPaymentTbFailed(ErrorCode):
    def __init__(self):
        super(GetPaymentTbFailed, self).__init__()
        self.result_code = 10002005
        self.result_msg = '取PAYMENT表出错'


class GetBillTbFailed(ErrorCode):
    def __init__(self):
        super(GetBillTbFailed, self).__init__()
        self.result_code = 10002006
        self.result_msg = '取BILL表出错'


class GetBillOweTbFailed(ErrorCode):
    def __init__(self):
        super(GetBillOweTbFailed, self).__init__()
        self.result_code = 10002007
        self.result_msg = '取BILL_OWE表出错'


class GetAggrTbFailed(ErrorCode):
    def __init__(self):
        super(GetAggrTbFailed, self).__init__()
        self.result_code = 10002008
        self.result_msg = '取AGGR表出错'


class UpdateNoneRecord(ErrorCode):
    def __init__(self):
        super(UpdateNoneRecord, self).__init__()
        self.result_code = 10002009
        self.result_msg = '更新记录数为零'


class DeputyNotExist(ErrorCode):
    def __init__(self):
        super(DeputyNotExist, self).__init__()
        self.result_code = 10002010
        self.result_msg = '账务代表号码不存在'


class LockTableFailed(ErrorCode):
    def __init__(self):
        super(LockTableFailed, self).__init__()
        self.result_code = 10002011
        self.result_msg = '锁表失败'


class CallInterfaceError(ErrorCode):
    def __init__(self):
        super(CallInterfaceError, self).__init__()
        self.result_code = 10002012
        self.result_msg = '调用远程服务接口失败'


if __name__ == '__main__':
    s = Success()
    print s.code
    print s.msg
    s.msg = '123'
    print s.code
    print s.msg
