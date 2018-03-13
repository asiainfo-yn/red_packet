# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Sequence, ForeignKey, Integer, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base, as_declarative, declared_attr
from sqlalchemy import func

Base = declarative_base()


class UserObjects(Base):
    __tablename__ = 'user_objects'

    object_name = Column(String(32), primary_key=True)
    object_type = Column(String(32))


class ABssOrgSwitch(Base):
    __tablename__ = 'a_bss_org_switch'

    switch_id = Column(Integer, primary_key=True)
    bss_org_id = Column(Integer)
    switch_value = Column(String(200))


class ASplitTableConfig(Base):
    __tablename__ = 'a_split_table_config'

    billing_cycle_id = Column(Integer, primary_key=True)
    table_type = Column(Integer, primary_key=True)
    table_name = Column(String(64))


class BInstTableList(Base):
    __tablename__ = 'b_inst_table_list'

    billing_cycle_id = Column(Integer, primary_key=True)
    billflow_id = Column(Integer, primary_key=True)
    table_type = Column(Integer, primary_key=True)
    org_id = Column(Integer, primary_key=True)
    table_name = Column(String(64))


class Serv(Base):
    __tablename__ = 'serv'

    serv_id = Column(Integer, primary_key=True)
    agreement_id = Column(Integer)
    cust_id = Column(Integer)
    product_id = Column(Integer)
    create_date = Column(DateTime)
    state = Column(String(3))
    state_date = Column(DateTime)
    rent_date = Column(DateTime)
    nsc_date = Column(DateTime)
    cycle_type_id = Column(Integer)
    billing_mode_id = Column(Integer)
    acc_nbr = Column(String(32))
    free_type_id = Column(Integer)


class Acct(Base):
    __tablename__ = 'acct'

    acct_id = Column(Integer, primary_key=True)
    cust_id = Column(Integer)
    acct_name = Column(String(200))
    address_id = Column(Integer)
    state = Column(String(3))
    state_date = Column(DateTime)
    acct_nbr_97 = Column(String(30))
    abm_flag = Column(String(1))
    batch_billing_cycle_id = Column(Integer)


class Cust(Base):
    __tablename__ = 'cust'

    cust_id = Column(Integer, primary_key=True)
    cust_name = Column(String(250))
    cust_type_id = Column(Integer)
    cust_location = Column(Integer)
    is_vip = Column(String(1))
    parent_id = Column(Integer)
    cust_code = Column(String(32))
    state = Column(String(3))
    eff_date = Column(DateTime)
    exp_date = Column(DateTime)
    brand_id = Column(Integer)


class ServAcct(Base):
    __tablename__ = 'serv_acct'

    acct_id = Column(Integer, primary_key=True)
    serv_id = Column(Integer, primary_key=True)
    item_group_id = Column(Integer)
    bill_require_id = Column(Integer)
    invoice_require_id = Column(Integer)
    payment_rule_id = Column(Integer)
    state = Column(String(3), primary_key=True)
    state_date = Column(DateTime)
    serv_acct_id = Column(Integer)
    created_date = Column(DateTime)


class ServLocation(Base):
    __tablename__ = 'serv_location'

    serv_id = Column(Integer, primary_key=True)
    agreement_id = Column(Integer, primary_key=True)
    address_id = Column(Integer)
    eff_date = Column(DateTime)
    exp_date = Column(DateTime)
    org_id = Column(Integer)


class Org(Base):
    __tablename__ = 'org'

    org_id = Column(Integer, primary_key=True)
    org_level_id = Column(Integer)
    name = Column(String(64))
    parent_org_id = Column(Integer)
    org_code = Column(String(12))
    org_area_code = Column(String(23))


class BillingCycle(Base):
    __tablename__ = 'billing_cycle'

    billing_cycle_id = Column(Integer, primary_key=True)
    billing_cycle_type_id = Column(Integer)
    cycle_begin_date = Column(DateTime)
    cycle_end_date = Column(DateTime)
    due_date = Column(DateTime)
    block_date = Column(DateTime)
    last_billing_cycle_id = Column(Integer)
    state = Column(String(3))
    state_date = Column(DateTime)


class AAcctOweState(Base):
    __tablename__ = 'a_acct_owe_state'

    acct_id = Column(Integer, primary_key=True)
    billing_cycle_id = Column(Integer, primary_key=True)
    state = Column(String(3))
    state_date = Column(DateTime)
    sum_owe = Column(Integer)
    payed = Column(Integer)
    state_detail = Column(String(100))


class ProdOfferInsAttr(Base):
    __tablename__ = 'product_offer_instance_attr'

    offer_attr_inst_id = Column(Integer, primary_key=True)
    agreement_id = Column(Integer)
    product_offer_instance_id = Column(Integer)
    attr_id = Column(Integer)
    attr_val = Column(Integer)
    eff_date = Column(DateTime)
    exp_date = Column(DateTime)


class BalancePayout(Base):
    __tablename__ = 'balance_payout'

    oper_payout_id = Column(Integer, primary_key=True)
    acct_balance_id = Column(Integer)
    billing_cycle_id = Column(Integer)
    bill_id = Column(Integer)
    oper_type = Column(String(3))
    staff_id = Column(Integer)
    oper_ = Column(DateTime)
    amount = Column(Integer)
    balance = Column(Integer)
    prn_count = Column(Integer)
    state = Column(String(3))
    state_ = Column(DateTime)
    bill_id2 = Column(Integer)


@as_declarative()
class AcctItemOweBase(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    acct_item_id = Column(Integer, primary_key=True)
    item_source_id = Column(Integer)
    bill_id = Column(Integer)
    acct_item_type_id = Column(Integer)
    billing_cycle_id = Column(Integer)
    acct_id = Column(Integer)
    serv_id = Column(Integer)
    amount = Column(Integer)
    created_date = Column(DateTime)
    fee_cycle_id = Column(Integer)
    payment_method = Column(Integer)
    state = Column(String(3))
    state_date = Column(DateTime)
    inv_offer = Column(String(3))
    offer_id = Column(Integer)
    ori_acct_item_id = Column(Integer)
    invoice_id = Column(Integer)
    corpus_flag = Column(String(3))


@as_declarative()
class BillBase(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    bill_id = Column(Integer, primary_key=True)
    operated_bill_id = Column(Integer)
    payment_id = Column(Integer)
    payment_method = Column(Integer)
    billing_cycle_id = Column(Integer)
    acct_id = Column(Integer)
    serv_id = Column(Integer)
    acc_nbr = Column(String(32))
    bill_amount = Column(Integer)
    late_fee = Column(Integer, default=0)
    derate_late_fee = Column(Integer, default=0)
    balance = Column(Integer, default=0)
    deposit_amount = Column(Integer, default=0)
    last_change = Column(Integer, default=0)
    cur_change = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now())
    payment_date = Column(DateTime, default=func.now())
    use_derate_blance = Column(Integer, default=0)
    invoice_id = Column(Integer)
    staff_id = Column(Integer)
    state = Column(String(3))
    state_date = Column(DateTime, default=func.now())


@as_declarative()
class PaymentBase(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    payment_id = Column(Integer, primary_key=True)
    acct_id = Column(Integer)
    payment_method = Column(Integer)
    payed_method = Column(Integer)
    operation_type = Column(String(3))
    operated_payment_serial_nbr = Column(Integer)
    amount = Column(Integer)
    payment_date = Column(DateTime, default=func.now())
    state = Column(String(3))
    state_date = Column(DateTime, default=func.now())
    created_date = Column(DateTime, default=func.now())
    staff_id = Column(Integer)
    serv_id = Column(Integer)
    acc_nbr = Column(String(32))
    pay_cycle_id = Column(Integer)


@as_declarative()
class ABillOweBase(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    acct_item_id = Column(Integer, primary_key=True)
    item_source_id = Column(Integer)
    bill_id = Column(Integer)
    acct_item_type_id = Column(Integer)
    billing_cycle_id = Column(Integer)
    acct_id = Column(Integer)
    serv_id = Column(Integer)
    amount = Column(Integer)
    created_date = Column(DateTime, default=func.now())
    fee_cycle_id = Column(Integer)
    payment_method = Column(Integer)
    state = Column(String(3))
    state_date = Column(DateTime, default=func.now())
    inv_offer = Column(String(3))
    offer_id = Column(Integer)
    ori_acct_item_id = Column(Integer)
    invoice_id = Column(Integer)
    corpus_flag = Column(String(3))


@as_declarative()
class AcctItemAggrBase(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    acct_item_id = Column(Integer, primary_key=True)
    acct_id = Column(Integer)
    charge = Column(Integer)


class BPresentResultHisLog(Base):
    __tablename__ = 'b_present_result_his_log'

    acct_item_id = Column(Integer, primary_key=True)
    acct_balance_id = Column(Integer)
    present_detail_id = Column(Integer)
    serv_id = Column(Integer)
    billing_cycle_id = Column(Integer)
    charge = Column(Integer)
    acct_id = Column(Integer)
    state = Column(String(3))
    state_date = Column(DateTime)
    present_method = Column(Integer)


class APresentDetail(Base):
    __tablename__ = 'a_present_detail'

    present_detail_id = Column(Integer, primary_key=True)
    acct_balance_id = Column(Integer)
    acct_id = Column(Integer)
    serv_id = Column(Integer)
    org_item_group_id = Column(Integer)
    des_item_group_id = Column(Integer)
    present_total_charge = Column(Integer)
    present_left_charge = Column(Integer)
    present_method = Column(Integer)
    present_lower = Column(Integer)
    present_upper = Column(Integer)
    eff_date = Column(DateTime)
    exp_date = Column(DateTime)
    area_code = Column(String(4))
    in_balance_flag = Column(Integer)
    offer_id = Column(Integer)
    offer_inst_id = Column(Integer)


class ProductOffer(Base):
    __tablename__ = 'product_offer'

    offer_id = Column(Integer, primary_key=True)
    pricing_plan_id = Column(Integer)
    offer_name = Column(String(128))
    offer_description = Column(String(4000))
    can_be_buy_alone = Column(String(3))
    offer_code = Column(String(20))
    state = Column(String(3))
    eff_date = Column(DateTime)
    exp_date = Column(DateTime)
    offer_type = Column(Integer)
    create_date = Column(DateTime)
    offer_priority = Column(Integer)
    billing_mode_id = Column(Integer)
    org_id = Column(Integer)
    brand_id = Column(Integer)
    offer_query_name = Column(String(128))
    agreement_length = Column(Integer)


class ProductOfferInstance(Base):
    __tablename__ = 'product_offer_instance'

    product_offer_instance_id = Column(Integer, primary_key=True)
    cust_id = Column(Integer)
    cust_agreement_id = Column(Integer)
    product_offer_id = Column(Integer)
    eff_date = Column(DateTime)
    state = Column(String(3))
    state_date = Column(DateTime)
    exp_date = Column(DateTime)
    belong_object_type = Column(String(3))
    belong_object_id = Column(Integer)


class ProductOfferInstanceWing(Base):
    __tablename__ = 'product_offer_instance_wing'

    seq_wing = Column(Integer, primary_key=True)
    product_offer_instance_id = Column(Integer)
    serv_id = Column(Integer)
    billing_mode_id = Column(Integer)
    wing_payment_id = Column(String(32))
    wing_total_charge = Column(Integer)
    eff_date = Column(DateTime)
    exp_date = Column(DateTime)
    state = Column(Integer)
    deal_state = Column(String(5))
    create_date = Column(DateTime)
    state_date = Column(DateTime)
    trade_reqo = Column(String(30))
    reverse_reqo = Column(String(30))
    remark = Column(String(100))
    upload_flag = Column(Integer)


class ACloudDataLoad(Base):
    __tablename__ = 'a_cloud_data_load'

    cloud_id = Column(Integer, primary_key=True)
    serv_id = Column(Integer)


class BEcsAcctData(Base):
    __tablename__ = 'b_ecs_acct_data'

    record_seq = Column(Integer, primary_key=True)
    acc_nbr = Column(String(32))
    serv_id = Column(Integer)
    bill_id = Column(Integer)
    billing_cycle = Column(Integer)


class TaxPayer(Base):
    __tablename__ = 'tax_payer'

    tax_payer_id = Column(Integer, primary_key=True)
    cust_id = Column(Integer)
    tax_payer_nbr = Column(String(20))
    name = Column(String(100))
    address = Column(String(250))
    acct_nbr = Column(String(100))
    bank_name = Column(String(100))
    bank_acct = Column(String(100))
    eff_date = Column(DateTime)
    exp_date = Column(DateTime)
    state_date = Column(DateTime)
    tax_invoice_flag = Column(Integer)


class AModifyTaxApi(Base):
    __tablename__ = 'a_modify_tax_api'

    modify_id = Column(Integer, Sequence('MODIFY_ID_SEQ'), primary_key=True)
    acct_id = Column(Integer)
    payment_id = Column(Integer)
    bill_id = Column(Integer)
    modify_type = Column(Integer)
    act_flag = Column(String(1))
    state = Column(String(3))
    state_date = Column(DateTime, default=func.now())
    create_date = Column(DateTime, default=func.now())
    err_code = Column(String(12))
    err_message = Column(String(255))


class AModifyTaxApiHis(Base):
    __tablename__ = 'a_modify_tax_api_his'

    modify_id = Column(Integer, primary_key=True)
    acct_id = Column(Integer)
    payment_id = Column(Integer)
    bill_id = Column(Integer)
    modify_type = Column(Integer)
    act_flag = Column(String(1))
    state = Column(String(3))
    state_date = Column(DateTime)
    create_date = Column(DateTime)
    err_code = Column(String(12))
    err_message = Column(String(255))


class AAcctDeputy(Base):
    __tablename__ = 'a_acct_deputy'

    acct_id = Column(Integer, primary_key=True)
    acc_nbr = Column(String(32))
    state_date = Column(DateTime)
    serv_id = Column(Integer)


class AChargeAdjustAudit(Base):
    __tablename__ = 'a_charge_adjust_audit'

    adjust_audit_log_id = Column(Integer, primary_key=True)
    acct_id = Column(Integer)
    serv_id = Column(Integer)
    acct_item_type_id = Column(Integer)
    charge = Column(Integer)
    adjust_acct_item_type_id = Column(Integer)
    adjust_type = Column(String(20))
    adjust_value = Column(Integer)
    billing_cycle_id = Column(Integer)
    apply_staff_id = Column(Integer)
    apply_date = Column(DateTime, default=func.now())
    audit_staff_id = Column(Integer)
    audit_reason = Column(String(250))
    audit_date = Column(DateTime, default=func.now())
    reverse_staff_id = Column(Integer)
    reverse_reason = Column(String(250))
    reverse_date = Column(DateTime)
    state = Column(String(3))
    adjust_apply_flag = Column(String(3))
    is_fore_adjust = Column(String(2))
    adjust_billing_cycle_id = Column(Integer)
    duty_org_id = Column(Integer)
    adjust_reason = Column(String(250))
    offer_id = Column(Integer)
    acct_item_state = Column(String(3))
    adjust_reason_append = Column(String(400))
    object_type_id = Column(Integer)
    item_group_id = Column(Integer)
    ori_adjust_audit_log_id = Column(Integer)


class AChargeAdjustLog(Base):
    __tablename__ = 'a_charge_adjust_log'

    adjust_log_id = Column(Integer, primary_key=True)
    acct_id = Column(Integer)
    serv_id = Column(Integer)
    acct_item_type_id = Column(Integer)
    adjust_type = Column(String(30))
    adjust_charge = Column(Integer)
    billing_cycle_id = Column(Integer)
    staff_id = Column(Integer)
    adjust_audit_log_id = Column(Integer, ForeignKey(AChargeAdjustAudit.adjust_audit_log_id))
    adjust_date = Column(DateTime, default=func.now())
    state = Column(String(3))
    acct_item_id = Column(Integer)
    is_fore_adjust = Column(String(2))
    adjust_reason = Column(String(250))
    offer_id = Column(Integer)
    acct_item_state = Column(String(3))


class AcctItemAdjustDetail(Base):
    __tablename__ = 'acct_item_adjust_detail'

    adjust_audit_log_id = Column(Integer, primary_key=True)
    acct_item_type_id = Column(Integer, primary_key=True)
    amount = Column(Integer)
    acct_item_adjust_type_id = Column(Integer)
    charge = Column(Integer)
    serv_id = Column(Integer)
    acct_id = Column(Integer)


class AAgentPayLog(Base):
    __tablename__ = 'a_agent_pay_log'

    nslc_id = Column(Integer, primary_key=True)
    payment_id = Column(Integer)
    request_no = Column(String(32))
    bill_result = Column(String(16))
    pay_result = Column(String(16))
    create_date = Column(DateTime)
    oper_type = Column(Integer, primary_key=True)
    amount = Column(Integer)
    pay_plat_form = Column(String(8))
