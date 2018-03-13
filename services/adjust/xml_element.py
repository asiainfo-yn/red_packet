# -*- coding:utf8 -*-
from public_class.convert_xml import Basic, ConvertXML


class RequestCashRoot(Basic):
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
        self.SOURCE_DESC = None


class RequestReverseRoot(Basic):
    __name__ = 'RequestRoot'

    def __init__(self):
        self.NSLC_ID = None
        self.STAFF_ID = None
        self.PAYMENT_CHARGE = None
