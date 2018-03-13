# -*- coding:utf8 -*-
from defines.app_errors import *


class OweChargeLow(ErrorCode):
    def __init__(self):
        super(OweChargeLow, self).__init__()
        self.result_code = 10001000
        self.result_msg = '出账金额低于套餐值'


class OweNotCharge(ErrorCode):
    def __init__(self):
        super(OweNotCharge, self).__init__()
        self.result_code = 10001001
        self.result_msg = '账期欠费'


class MainDateNotEffect(ErrorCode):
    def __init__(self):
        super(MainDateNotEffect, self).__init__()
        self.result_code = 10001002
        self.result_msg = '主套餐未生效'


class RedDateNotEffect(ErrorCode):
    def __init__(self):
        super(RedDateNotEffect, self).__init__()
        self.result_code = 10001003
        self.result_msg = '红包套餐未生效'


class PresentMethodNotFound(ErrorCode):
    def __init__(self):
        super(PresentMethodNotFound, self).__init__()
        self.result_code = 10001004
        self.result_msg = '赠送规则未找到，请确定赠送月数是否超过期限'


class MainEffExpNone(ErrorCode):
    def __init__(self):
        super(MainEffExpNone, self).__init__()
        self.result_code = 10001005
        self.result_msg = '主套餐生效时间不能为空'


class RedEffExpOverdue(ErrorCode):
    def __init__(self):
        super(RedEffExpOverdue, self).__init__()
        self.result_code = 10001006
        self.result_msg = '红包套餐生效日期已超赠送月数-修正失败'


class RedUserNotFound(ErrorCode):
    def __init__(self):
        super(RedUserNotFound, self).__init__()
        self.result_code = 10001007
        self.result_msg = '红包用户未找到'


class HasRecord(ErrorCode):
    def __init__(self):
        super(HasRecord, self).__init__()
        self.result_code = 10001008
        self.result_msg = '赠送结果表中已有数据'


class RePresentSuccess(ErrorCode):
    def __init__(self):
        super(RePresentSuccess, self).__init__()
        self.result_code = 10001009
        self.result_msg = '交清欠费，补送成功'


class FinishedExpire(ErrorCode):
    def __init__(self):
        super(FinishedExpire, self).__init__()
        self.result_code = 10001010
        self.result_msg = '已经送完所有红包'


class FinishedOwe3Month(ErrorCode):
    def __init__(self):
        super(FinishedOwe3Month, self).__init__()
        self.result_code = 10001011
        self.result_msg = '欠费已达三个月，永不赠送'


class FinishedOffline(ErrorCode):
    def __init__(self):
        super(FinishedOffline, self).__init__()
        self.result_code = 10001012
        self.result_msg = '用户已拆机'


class TerminalExpNotAllow(ErrorCode):
    def __init__(self):
        super(TerminalExpNotAllow, self).__init__()
        self.result_code = 10001013
        self.result_msg = '终端款套餐不能有失效日期'


class TerminalAmountOverflow(ErrorCode):
    def __init__(self):
        super(TerminalAmountOverflow, self).__init__()
        self.result_code = 10001014
        self.result_msg = '总赠送金额已达终端款'


class EffExpEqual(ErrorCode):
    def __init__(self):
        super(EffExpEqual, self).__init__()
        self.result_code = 10001015
        self.result_msg = '红包套餐生失效时间相同'


class EarlierOfferExist(ErrorCode):
    def __init__(self):
        super(EarlierOfferExist, self).__init__()
        self.result_code = 10001016
        self.result_msg = '存在生效时间更早的红包套餐'


class PremiseOfferInfoNotExist(ErrorCode):
    def __init__(self):
        super(PremiseOfferInfoNotExist, self).__init__()
        self.result_code = 10001017
        self.result_msg = '没有对应的主套餐信息'


class AttrIdNotExist(ErrorCode):
    def __init__(self):
        super(AttrIdNotExist, self).__init__()
        self.result_code = 10001018
        self.result_msg = '没有对应的套餐参数信息'


class AttrInstValNotExist(ErrorCode):
    def __init__(self):
        super(AttrInstValNotExist, self).__init__()
        self.result_code = 10001019
        self.result_msg = '没有对应的套餐参数'
