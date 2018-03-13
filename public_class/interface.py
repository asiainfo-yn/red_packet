# -*- coding: UTF-8 -*-
import logging
from xml.etree import ElementTree as ET
from tornado.httpclient import HTTPClient
from convert_xml import *
from defines.app_errors import *


def call_cash_bill_intf(url, xml_obj):
    """
    调用计费接口
    :param url:
    :param xml_obj:
    :return:
    """
    logging.info('start call reverse intf')

    xml_str = ConvertXML(xml_obj).toxml()
    client = HTTPClient()
    response = client.fetch(url, method='POST', body=xml_str)
    xml_res = response.body

    if xml_res is None:
        raise MyException(CallInterfaceError())

    # 解析返回数据
    xml_res = xml_res.decode('gbk').encode('utf-8')
    parser = ET.XMLParser(target=ET.TreeBuilder(), encoding='utf-8')
    root = ET.fromstring(xml_res, parser=parser)
    code = root.findtext('Result')
    mark = root.findtext('ResultMark')
    pay_id = root.findtext('PAYMENT_ID')
    nslc_id = root.findtext('NSLC_ID')

    logging.info('-'.join(['end call reverse intf', code, mark]))

    return code, mark, pay_id, nslc_id
