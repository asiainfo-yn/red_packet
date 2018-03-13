# -*- coding: UTF-8 -*-
from public_modules.models import *

RESULT_MSG_LEN = 128


class ARedPacketUser(Base):
    __tablename__ = 'a_red_packet_user'

    red_id = Column(Integer, primary_key=True)
    serv_id = Column(Integer)
    premise_eff_date = Column(DateTime)
    premise_exp_date = Column(DateTime)
    wing_eff_date = Column(DateTime)
    wing_exp_date = Column(DateTime)
    premise_offer_inst_id = Column(Integer)
    wing_offer_inst_id = Column(Integer)
    finish_flag = Column(Integer)
    rule_id = Column(Integer)
    upload_flag = Column(Integer)


class ARedPacket(Base):
    __tablename__ = 'a_red_packet'

    packet_id = Column(Integer, Sequence('seq_red_packet_id'), primary_key=True)
    red_id = Column(Integer)
    area_name = Column(String(32))
    bss_type = Column(String(32), default='翼支付红包套餐'.decode('utf-8').encode('gbk'))
    main_offer_name = Column(String(128))
    main_eff_date = Column(DateTime)
    main_charge = Column(Numeric(16, 5))
    red_offer_id = Column(Integer)
    red_offer_name = Column(String(128))
    red_eff_date = Column(DateTime)
    acc_nbr = Column(String(32))
    cust_name = Column(String(250))
    reqnumtype = Column(String(8))
    acct_month = Column(String(6))
    red_charge = Column(Numeric(16, 5))
    create_date = Column(DateTime, default=func.now())
    serial_nbr = Column(Integer, Sequence('seq_red_packet_serial'))
    state = Column(String(3))
    state_date = Column(DateTime, default=func.now())
    acct_id = Column(Integer)
    bill_amount = Column(Integer)
    action_type = Column(Integer)
    discount_value = Column(Integer)


class ARedPacketPercent(Base):
    __tablename__ = 'a_red_packet_percent'

    red_id = Column(Integer, primary_key=True)
    serv_id = Column(Integer)
    billing_cycle_id = Column(Integer)
    fix_charge = Column(Integer)
    percent_type = Column(Integer)
    org_id = Column(Integer)
    create_date = Column(DateTime, default=func.now())
    percent_flag = Column(Integer)


class ARedPacketBs(Base):
    __tablename__ = 'a_red_packet_bs'

    red_id = Column(Integer, primary_key=True)


class ARedPacketResult(Base):
    __tablename__ = 'a_red_packet_result'

    red_id = Column(Integer, primary_key=True)
    acc_nbr = Column(String(32))
    # area_code = Column(String(4))
    acct_month = Column(String(6), primary_key=True)
    packet_id = Column(Integer)
    create_date = Column(DateTime, default=func.now())
    msg = Column(String(RESULT_MSG_LEN))


class ARedPacketOfferPresent(Base):
    __tablename__ = 'a_red_packet_offer_present'

    offer_id = Column(Integer, primary_key=True)
    offer_name = Column(String(128))


class ARedPacketUpload(Base):
    __tablename__ = 'a_red_packet_upload'

    red_id = Column(Integer, primary_key=True)
    upload_flag = Column(Integer, primary_key=True)
    create_date = Column(DateTime, default=func.now())
    remark = Column(String(128))
    req_xml = Column(String(1024))
    red_type = Column(Integer)


class ARedPacketMethod(Base):
    __tablename__ = 'a_red_packet_method'

    method_id = Column(Integer, primary_key=True)
    base = Column(Integer)
    method = Column(Integer)
    discount_flag = Column(Integer)
    terminal_flag = Column(Integer)
    description = Column(String(128))


class ARedPacketAttr(Base):
    __tablename__ = 'a_red_packet_attr'

    attr_id = Column(Integer, primary_key=True)
    attr_type = Column(Integer)
    product_offer_attr_id = Column(Integer, primary_key=True)


class TifOfferForExWing(Base):
    __tablename__ = 'tif_offer_for_ex_wing'

    rule_id = Column(Integer, primary_key=True)
    premise_offer_id = Column(Integer)
    premise_offer_name = Column(String(300))
    premise_plan_amount = Column(Numeric(12, 3))
    wing_offer_id = Column(Integer)
    wing_offer_name = Column(String(300))
    wing_cycle_upper = Column(Numeric(12, 3))
    # create_date = Column(DateTime)
    # present_method = Column(String(8), primary_key=True)
    # premise_flag = Column(Integer)
    # wing_attr_type = Column(Integer)
    attr_id = Column(Integer)
    method_id = Column(Integer)
    month_range = Column(String(4), primary_key=True)

    def start_month(self):
        return int(self.month_range[0:2])

    def end_month(self):
        return int(self.month_range[2:4])

    '''
    @staticmethod
    def start_month():
        return func.to_number(func.substr(TifOfferForExWing.present_method, 3, 2))

    @staticmethod
    def end_month():
        return func.to_number(func.substr(TifOfferForExWing.present_method, 5, 2))
    '''


class CRedPacket(Base):
    __tablename__ = 'c_red_package'

    bill_packet_id = Column(Integer, primary_key=True)
    busi_order_id = Column(String(32))


class CPayOrder(Base):
    __tablename__ = 'c_pay_order'

    busi_order_id = Column(String(32), primary_key=True)
    platform_id = Column(String(32))
    pay_status = Column(Integer)
    pay_result = Column(Integer)
    remark = Column(String(32))
