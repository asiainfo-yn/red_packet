# -*- coding:utf8 -*-
from public_class.convert_xml import Basic, ConvertXML


class ContractRoot(Basic):
    __name__ = 'ContractRoot'

    def __init__(self):
        self.tcp_cont = TcpCont()
        self.svc_cont = SvcCont()


class TcpCont(Basic):
    __name__ = 'TcpCont'

    def __init__(self):
        self.SrcTransactionNbr = 'AT'
        self.ServiceCode = 'rePayService'
        self.SrcSysID = 'JF'
        self.SrcSysSign = 'jf123'
        self.ReqTime = None


class SvcCont(Basic):
    __name__ = 'SvcCont'

    def __init__(self):
        self.ct_root = CtRoot()


class CtRoot(Basic):
    __name__ = 'ctroot'

    def __init__(self):
        self.reqplatform = 'BILL'
        self.payplatform = 'ALIPAY'
        self.reqpaytype = ''
        self.timestamp = ''
        self.reqno = ''
        self.requser = ''
        self.reqnumtype = '1'
        self.reqnum = ''
        self.areacode = ''
        self.payamount = ''
        self.sign = ''
