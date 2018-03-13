# -*- coding:utf8 -*-
from defines.app_errors import *

CODE_HEAD = 10004000


class XmlParseError(ErrorCode):
    def __init__(self):
        super(XmlParseError, self).__init__()
        self.result_code = CODE_HEAD + 1
        self.result_msg = '解析xml失败'


class CallProcedureError(ErrorCode):
    def __init__(self):
        super(CallProcedureError, self).__init__()
        self.result_code = CODE_HEAD + 2
        self.result_msg = '存储过程返回错误'


class AdjustInterfaceError(ErrorCode):
    def __init__(self):
        super(AdjustInterfaceError, self).__init__()
        self.result_code = CODE_HEAD + 3
        self.result_msg = '调账接口返回失败'


class AdjustAmountIsZero(ErrorCode):
    def __init__(self):
        super(AdjustAmountIsZero, self).__init__()
        self.result_code = CODE_HEAD + 4
        self.result_msg = '调账金额为零'


class AdjustNslcNotFound(ErrorCode):
    def __init__(self):
        super(AdjustNslcNotFound, self).__init__()
        self.result_code = CODE_HEAD + 5
        self.result_msg = 'NslcId不存在'


class AdjustLogNotFound(ErrorCode):
    def __init__(self):
        super(AdjustLogNotFound, self).__init__()
        self.result_code = CODE_HEAD + 5
        self.result_msg = '调账日志不存在'
