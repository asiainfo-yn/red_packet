# -*- coding:utf8 -*-
from defines.app_errors import *


class OweInfoNotExist(ErrorCode):
    def __init__(self):
        super(OweInfoNotExist, self).__init__()
        self.result_code = 10003000
        self.result_msg = '欠费信息不存在'


class PreChargeUserExist(ErrorCode):
    def __init__(self):
        super(PreChargeUserExist, self).__init__()
        self.result_code = 10003001
        self.result_msg = '存在预付费用户'


class OtherTrustRecordExist(ErrorCode):
    def __init__(self):
        super(OtherTrustRecordExist, self).__init__()
        self.result_code = 10003002
        self.result_msg = '存在其他托收记录'


class OweFeeNotTrust(ErrorCode):
    def __init__(self):
        super(OweFeeNotTrust, self).__init__()
        self.result_code = 10003100
        self.result_msg = '费用未托收'


class OweFeeNETrustFee(ErrorCode):
    def __init__(self):
        super(OweFeeNETrustFee, self).__init__()
        self.result_code = 10003101
        self.result_msg = '销账金额和托收金额不相等'


class TrustAmountIsZero(ErrorCode):
    def __init__(self):
        super(TrustAmountIsZero, self).__init__()
        self.result_code = 10003102
        self.result_msg = '托收金额为零'


class AlipayIntfError(ErrorCode):
    def __init__(self):
        super(AlipayIntfError, self).__init__()
        self.result_code = 10003103
        self.result_msg = '支付宝代扣失败'


class XmlParseError(ErrorCode):
    def __init__(self):
        super(XmlParseError, self).__init__()
        self.result_code = 10003104
        self.result_msg = '解析xml失败'


class SignValidateError(ErrorCode):
    def __init__(self):
        super(SignValidateError, self).__init__()
        self.result_code = 10003105
        self.result_msg = '数字签名验证失败'
