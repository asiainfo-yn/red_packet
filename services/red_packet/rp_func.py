# -*- coding: UTF-8 -*-
from decimal import Decimal
from modules import *
from defines.variables import *
from defines.app_errors import *
from public_modules.acct_item_owe import *
from public_modules.acct_item_aggr_hb import *


def get_offer_inst_attr_val(son, offer_inst_id, attr_id):
    """
    获取套餐实例参数
    :param offer_inst_id: 套餐实例ID
    :param attr_id: 套餐参数ID
    :return: 套餐参数值
    """
    return son.query(func.nvl(func.sum(ProdOfferInsAttr.attr_val), 0)).filter(
        ProdOfferInsAttr.product_offer_instance_id == offer_inst_id,
        ProdOfferInsAttr.attr_id == attr_id,
    ).order_by(ProdOfferInsAttr.exp_date.desc()).scalar()


def get_red_amount(son, rule, method, offer_inst_id, offer_attr_id):
    """
    获取需要赠送的金额
    :param son:db connection
    :param rule:赠送规则
    :param method:赠送方法
    :param offer_inst_id:套餐实例标识
    :param offer_attr_id:套餐实例属性标识
    :return:
    """
    amount = Decimal(0)

    if method.method == 0:
        # 固定值赠送
        amount = Decimal(rule.wing_cycle_upper)
    elif method.method == 1:
        # 比例赠送
        if method.base == 1:
            # 以主套餐为基数计算
            amount = Decimal(rule.wing_cycle_upper / 100) * Decimal(rule.premise_plan_amount)
        elif method.base == 2:
            # 以红包套餐套餐参数为基数计算
            amount = get_offer_inst_attr_val(son, offer_inst_id, offer_attr_id)
            amount = Decimal(amount / 100.0) * Decimal(rule.wing_cycle_upper / 100)
        else:
            logging.error('base not in (1,2)')
    elif method.method == 2:
        # 分段赠送，虽然配置表里配置了多条，但是处理方法可以同固定值赠送方式
        amount = Decimal(rule.wing_cycle_upper)
    else:
        logging.error('method not in (0,1,2)')

    return amount


def get_rule(rules, month_offset):
    """
    从多个规则中取出对应规则，一般适用于分段赠送
    :param rules: 规则列表
    :param month_offset: 当前赠送账期偏移数
    :return:
    """
    packet_rule = None
    packet_method = None
    for rule in rules:
        p_rule = rule.TifOfferForExWing
        p_method = rule.ARedPacketMethod
        s_month = p_rule.start_month()
        e_month = p_rule.end_month()

        if s_month + e_month == 0:
            packet_rule = p_rule
        elif s_month < month_offset <= e_month:
            packet_rule = p_rule
        elif month_offset == e_month + 1:
            packet_rule = p_rule

        if packet_rule is not None:
            packet_method = p_method
            break
    return packet_rule, packet_method


def get_attr_id(attrs, attr_type):
    """
    获取attrid
    :param attrs: ARedPacketAttr记录
    :param attr_type: 类型
    :return:
    """
    attr_id = None
    for attr in attrs:
        if attr.attr_type == attr_type:
            attr_id = attr.product_offer_attr_id
            break
    return attr_id


def get_owe_charge(son, acct_id, billing_cycle_id):
    """
    取出账金额-欠费表
    :param son:
    :param acct_id:
    :param billing_cycle_id:
    :return:
    """
    key = str(200000 + int(billing_cycle_id) - 10000)
    cls_owe = TB_ACCT_ITEM_OWE.get(key)
    if cls_owe is None:
        raise MyException(GetOweTbFailed())

    # 取欠费表金额（排除对冲金额）
    payout = son.query(BalancePayout.bill_id2).filter(
        cls_owe.bill_id == BalancePayout.bill_id2,
        cls_owe.item_source_id.in_([2, 5]),
        BalancePayout.oper_type == '5UJ'
    )

    owe_charge = son.query(func.nvl(func.sum(cls_owe.amount), 0)).filter(
        cls_owe.acct_id == acct_id,
        ~payout.exists()
        # cls_owe.state == '5JB'--不判断是否销账
    ).scalar()

    # 取特殊赠送费用，ARedPacketOfferPresent 为特殊赠送套餐配置表
    red_present = son.query(ARedPacketOfferPresent.offer_id)

    present_detail = son.query(APresentDetail.present_detail_id).filter(
        APresentDetail.present_detail_id == BPresentResultHisLog.present_detail_id,
        APresentDetail.offer_id.in_(red_present)
    )

    owe_charge += son.query(func.nvl(func.sum(BPresentResultHisLog.charge), 0)).filter(
        present_detail.exists(),
        BPresentResultHisLog.acct_id == acct_id,
        BPresentResultHisLog.billing_cycle_id == billing_cycle_id
    ).scalar()

    return owe_charge / 100.0


def get_aggr_charge(son, acct_id, billing_cycle_id, org_id):
    """
    取出账金额-总账表（分成用）
    :param son:
    :param acct_id:
    :param billing_cycle_id:
    :param org_id:
    :return:
    """
    key = ''.join([str(billing_cycle_id), '_', str(org_id)])
    cls_aggr = TB_ACCT_ITEM_AGGR_HB.get(key)
    if cls_aggr is None:
        raise MyException(GetOweTbFailed())

    owe_charge = son.query(func.nvl(func.sum(cls_aggr.charge), 0)).filter(
        cls_aggr.acct_id == acct_id,
    ).scalar()

    return owe_charge / 100.0


def get_area_code(son, serv_id):
    """
    取用户区号
    :param serv_id:
    :return:
    """
    return son.query(Org).join(
        ServLocation, ServLocation.org_id == Org.org_id
    ).filter(
        ServLocation.serv_id == serv_id,
        ServLocation.eff_date <= func.now(),
        ServLocation.exp_date >= func.now()
    ).with_entities(Org.org_area_code).scalar()


'''
def get_org_id(son, serv_id):
    """
    取用户局向
    :param serv_id:
    :return:
    """
    org_id = son.query(ServLocation.org_id).filter(
        ServLocation.serv_id == serv_id,
    ).order_by(ServLocation.exp_date.desc()).limit(1).scalar()

    sql = ''.join([
        'SELECT ORG_ID',
        '  FROM ORG',
        ' WHERE ORG_LEVEL_ID = 200',
        ' START WITH ORG_ID = ', str(org_id),
        ' CONNECT BY PRIOR PARENT_ORG_ID = ORG_ID',
    ])
    return son.execute(sql).scalar()
'''


def get_all_charge(son, rules, offer_inst_id, attr_id):
    """
    获取赠送规则总赠送金额-除终端款和套餐无失效日期的用户
    :param son:
    :param rules: 赠送规则列表
    :param offer_inst_id: 红包套餐实例
    :param attr_id: 红包套餐参数id
    :return:
    """
    red_all_charge = Decimal(0)
    for r in rules:
        # 按（金额*月数）计算
        r_rule = r.TifOfferForExWing
        r_method = r.ARedPacketMethod
        month_num = r_rule.end_month() - r_rule.start_month()
        red_amount = get_red_amount(son, r_rule, r_method, offer_inst_id, attr_id)
        red_all_charge += Decimal(round(red_amount, 1) * month_num)

    return red_all_charge


def cal_discount(cycle, c_time, flag):
    """
    计算套餐在赠送账期内的折扣值
    :param cycle:
    :param c_time:
    :param flag: 0：生效月份，others：失效月份
    :return:
    """
    if cycle.cycle_begin_date <= c_time < cycle.cycle_end_date:
        if flag == 0:
            offer_days = (cycle.cycle_end_date - c_time).days + 1
        else:
            offer_days = (c_time - cycle.cycle_begin_date).days
        cycle_days = (cycle.cycle_end_date - cycle.cycle_begin_date).days
        value = Decimal(offer_days) / Decimal(cycle_days)
        if value > 1:
            value = Decimal(1.0)
    else:
        value = Decimal(1.0)

    return value


def get_discount(cycle, user, premise_flag):
    """
    获取当前赠送账期的折扣值，计算时取主套餐和红包套餐生失效时间的交集
    :param cycle:
    :param user:
    :param premise_flag: 是否有主套餐标识
    :return:
    """
    w_eff_date = user.wing_eff_date
    w_exp_date = user.wing_exp_date
    p_eff_date = user.premise_eff_date
    p_exp_date = user.premise_exp_date

    eff_time = w_eff_date if premise_flag == 0 \
        else max(w_eff_date, p_eff_date)
    exp_time = w_exp_date if premise_flag == 0 \
        else min(w_exp_date, p_exp_date)

    # 分别计算生效和失效时候的折扣值
    dis_eff_value = cal_discount(cycle, eff_time, 0)
    dis_exp_value = cal_discount(cycle, exp_time, 1)

    # 当月生效且当月失效的套餐取总生效天数的折扣
    # 否则取生效和失效折扣值中的最小值（因为账期的限制，最小值就是需要的折扣值）
    if eff_time.strftime('%Y%m') == exp_time.strftime('%Y%m'):
        dis_value = dis_eff_value + dis_exp_value - 1
    else:
        dis_value = min(dis_eff_value, dis_exp_value)

    return dis_value
