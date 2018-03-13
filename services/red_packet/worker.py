# -*- coding: UTF-8 -*-
from datetime import timedelta
from sqlalchemy.sql import select, and_
from rp_func import *
from public_class.async_func import AsyncModule, auto_release
from errors import *


__author__ = 'ym'


def gene_result(son, acc_nbr, red_id, packet_id, month, code, msg):
    """
    插入赠送结果表
    :param son:
    :param acc_nbr:
    :param red_id:
    :param packet_id: 
    :param month: 
    :param code: 
    :param msg: 
    :return: 
    """
    # 获取以前赠送结果，如果存在则更新，不存在则插入
    pkg_res = son.query(ARedPacketResult).filter(
        ARedPacketResult.acct_month == month,
        ARedPacketResult.red_id == red_id
    ).scalar()

    if pkg_res is None:
        red_pkg_res = ARedPacketResult()
        red_pkg_res.acc_nbr = acc_nbr
        red_pkg_res.acct_month = month
        red_pkg_res.msg = msg
        red_pkg_res.red_id = red_id
        red_pkg_res.packet_id = packet_id
        return red_pkg_res
    else:
        '''
        if code == UserOffLine().code:
            # 拆机数据不更新，否则会把所有月份赠送结果全部更新
            return None
        '''
        pkg_res.msg = msg
        pkg_res.create_date = func.now()
        pkg_res.packet_id = packet_id
        return pkg_res


def deal(son, user, cycle, action_type):
    """
    处理一个用户，单个账期内赠送
    :param son:
    :param user:
    :param cycle:
    :param action_type: 0：全量赠送，1：增量赠送（交清欠费补送），2：增量赠送（手动补送），3：分成
    :return:
    """
    sa = None
    packet_id = None
    result = VirSuccess()
    son_objects = list()
    action_type = int(action_type)

    logging.info('serv_id=%ld-start' % user.serv_id)
    month = ''.join(['20', str(cycle.billing_cycle_id)[1:]])

    # 判断用户状态是否正常
    try:
        sas = son.query(ServAcct).join(
            Serv, ServAcct.serv_id == Serv.serv_id
        ).filter(
            ~Serv.state.in_(['2HX', '2IX']),
            Serv.serv_id == user.serv_id
        ).add_entity(Serv).order_by(ServAcct.state_date.asc()).all()
        if sas is None or len(sas) == 0:
            user.finish_flag = FINISH_FLAG_OFF_LINE
            son_objects.append(user)
            raise MyException(UserOffLine())

        state_flag = STATE_P0P
        # 获取赠送账期内最后一次过户的acct_id，所以上面不能限制state字段
        for s in sas:
            if s.ServAcct.state_date > cycle.cycle_end_date:
                sa = s
                break
        if sa is None:
            raise MyException(GetAcctIdFailed())

        # 当天生效当天失效的不处理
        if user.wing_eff_date.strftime('%Y%m%d') == user.wing_exp_date.strftime('%Y%m%d'):
            raise MyException(EffExpEqual())

        # 判断主套餐在该账期内是否生效
        if user.premise_eff_date is not None and user.premise_eff_date >= cycle.cycle_end_date:
            raise MyException(MainDateNotEffect())
        if user.premise_exp_date is not None and user.premise_exp_date <= cycle.cycle_begin_date:
            raise MyException(MainDateNotEffect())
        # 判断红包套餐在该账期内是否生效
        if user.wing_eff_date >= cycle.cycle_end_date:
            raise MyException(RedDateNotEffect())
        if user.wing_exp_date <= cycle.cycle_begin_date:
            raise MyException(RedDateNotEffect())

        # 用户赠送月存在多个红包套餐，规则如下：
        # 1. 以生效时间早的为准
        # 2. 如果生效时间完全一样，则两个都不送
        # 3. 生效时间晚的仍然要生成数据到A_RED_PACKET表中，状态置为P0E
        # 4. 套餐送完或退订后不再更新finish_flag字段，以后在客户端控制需要赠送的用户
        user_packets = son.query(ARedPacketUser).filter(
            ARedPacketUser.serv_id == user.serv_id,
            ARedPacketUser.red_id != user.red_id,
            ARedPacketUser.finish_flag == FINISH_FLAG_NORMAL
        ).all()
        for user_packet in user_packets:
            if user_packet.wing_eff_date.strftime('%Y%m%d') == user_packet.wing_exp_date.strftime('%Y%m%d'):
                continue
            if user.wing_eff_date >= user_packet.wing_eff_date:
                # 存在更早订购的红包套餐
                # 减去一天，否则会因为套餐只生效一天赠送金额为零
                tmp_exp_date = user_packet.wing_exp_date - timedelta(days=1)
                '''
                if user.wing_eff_date < tmp_exp_date:
                    # 生效和失效时间上有交集，且交集范围大于一天内
                    state_flag = STATE_P0E
                elif user.wing_eff_date.strftime('%Y%m') == \
                        tmp_exp_date.strftime('%Y%m') == \
                        cycle.cycle_begin_date.strftime('%Y%m'):
                    # 后面的套餐有交集的月份不送红包
                    state_flag = STATE_P0E
                '''
                if tmp_exp_date >= cycle.cycle_begin_date:
                    # 多个套餐有重叠，则按老套餐计算，新套餐不送
                    state_flag = STATE_P0E

        # 取欠费状态
        if action_type == ACTION_TYPE_FC:
            owe_state = OWE_STATE_10X
            red_packet = None
        else:
            owe_state = son.query(func.nvl(AAcctOweState.state, OWE_STATE_10X)).filter(
                AAcctOweState.billing_cycle_id == cycle.billing_cycle_id,
                AAcctOweState.acct_id == sa.ServAcct.acct_id
            ).scalar()

            # 则判断该账期是否已经赠送红包
            red_packet = son.query(ARedPacket).filter(
                ARedPacket.acct_month == month,
                ARedPacket.red_id == user.red_id
            ).scalar()

        if red_packet is None:
            # 接口表没有记录，需要赠送，分成时必为空
            # 判断用户是否欠费
            if state_flag != STATE_P0E and owe_state != OWE_STATE_10X:
                state_flag = STATE_P0C

            # 取红包套餐对应关系
            present_year = (cycle.cycle_begin_date.year - user.wing_eff_date.year) * 12
            present_month = cycle.cycle_begin_date.month - user.wing_eff_date.month + present_year + 1

            packet_rules = son.query(TifOfferForExWing).join(
                ARedPacketMethod, ARedPacketMethod.method_id == TifOfferForExWing.method_id
            ).filter(
                TifOfferForExWing.rule_id == user.rule_id
            ).add_entity(ARedPacketMethod).all()

            # 获取赠送规则
            exp_flag = 1
            premise_flag = 1
            packet_rule, packet_method = get_rule(packet_rules, present_month)

            if packet_rule is None or packet_method is None:
                raise MyException(PresentMethodNotFound())

            # 取attr_id
            packet_attr = []
            if packet_rule.attr_id is not None:
                packet_attr = son.query(ARedPacketAttr).filter(
                    ARedPacketAttr.attr_id == packet_rule.attr_id
                ).all()

            if packet_rule.attr_id is not None and len(packet_attr) == 0:
                raise MyException(AttrIdNotExist())
            elif packet_method.base == 2 and len(packet_attr) == 0:
                raise MyException(AttrIdNotExist())

            if packet_rule.start_month() + packet_rule.end_month() == 0:
                exp_flag = 0
            if packet_rule.premise_offer_id is None:
                premise_flag = 0
            elif user.premise_eff_date is None or user.premise_exp_date is None:
                raise MyException(PremiseOfferInfoNotExist())

            premise_value = packet_rule.premise_plan_amount
            discount_flag = packet_method.discount_flag
            terminal_flag = packet_method.terminal_flag
            rule_base = packet_method.base
            bd_attr_id = get_attr_id(packet_attr, ATTR_TYPE_BD)
            zsje_attr_id = get_attr_id(packet_attr, ATTR_TYPE_ZSJE)

            if premise_value == Decimal(0) and rule_base == 2:
                # 对于有主套餐，且套餐值为空的数据，如果规则是以套餐参数为基数，则主套餐值取套餐参数
                premise_value = get_offer_inst_attr_val(son, user.wing_offer_inst_id, bd_attr_id)
                premise_value = premise_value / 100

            # 计算一个月返还值
            attr_id = bd_attr_id if zsje_attr_id is None else zsje_attr_id
            red_amount = get_red_amount(son, packet_rule, packet_method, user.wing_offer_inst_id, attr_id)

            # 判断红包套餐生效月数是否超过需赠送月数（1. 取相应的规则；2：避免于生失效时间有问题的套餐送红包）
            # 修正失效日期（用户最后一个月）
            last_rule = max(map(lambda r: r.TifOfferForExWing.end_month(), packet_rules))

            curr = cycle.cycle_begin_date
            wing_year = (user.wing_exp_date.year - user.wing_eff_date.year) * 12
            curr_year = (curr.year - user.wing_eff_date.year) * 12

            wing_month_num = user.wing_exp_date.month - user.wing_eff_date.month + wing_year + 1
            curr_month_num = curr.month - user.wing_eff_date.month + curr_year + 1
            if discount_flag == 1:
                # 首月全额赠送，所以套餐失效月不送红包
                rule_month_num = last_rule
            else:
                # 按日折算，赠送总月数要加1
                rule_month_num = last_rule + 1

            if exp_flag == 1 and wing_month_num > rule_month_num:
                # 有失效日期，且红包生效月数超过规则月数，进行修正
                wing_month_num = rule_month_num
                if curr_month_num > wing_month_num:
                    raise MyException(RedEffExpOverdue())

            # 计算折扣值，红包套餐赠送金额和主套餐套餐值折扣均按此值计算
            dis_value = get_discount(cycle, user, premise_flag)

            if discount_flag == 0 and curr_month_num == 1:
                # 折算方式是按日折算，且是第一个月--按日折算
                red_charge = dis_value * red_amount
            elif curr_month_num == wing_month_num:
                # 套餐末月和套餐退订月
                if exp_flag == 1 and wing_month_num == rule_month_num:
                    # 对于有有效期且正常失效套餐--取剩余赠送金额全部赠送
                    # 取需要赠送的全部金额
                    red_all_charge = get_all_charge(son, packet_rules, user.wing_offer_inst_id, attr_id)

                    # 取接口表中已经赠送的金额（包括所有状态）
                    red_pres_charge = son.query(func.nvl(func.sum(ARedPacket.red_charge), 0)).filter(
                        ARedPacket.red_id == user.red_id
                    ).scalar()
                    red_charge = red_all_charge - red_pres_charge
                    # 正常失效，判断是否还有欠费月份，如果没有则更新成永不赠送
                    count_p0c = son.query(func.count('*')).filter(
                        ARedPacket.red_id == user.red_id,
                        ARedPacket.state == STATE_P0X,
                    ).scalar()
                    if count_p0c == 0:
                        user.finish_flag = FINISH_FLAG_TERMINAL
                else:
                    # 对于没有有效期或套餐提前退订的套餐--按日折算
                    red_charge = dis_value * red_amount
                    # 提前退订，更新成永不赠送
                    user.finish_flag = FINISH_FLAG_TERMINAL
                '''
                # 最后一个月送完更新永不赠送标识，不在这里做了，放到补送程序里
                user.finish_flag = FINISH_FLAG_EXPIRE
                son_objects.append(user)
                '''
            else:
                # 中间月
                red_charge = red_amount

            if terminal_flag == 1:
                # 终端款用户重新计算金额
                if exp_flag == 0:
                    # 没有失效日期，且总赠送金额按终端款计算，要判断是否送完
                    zdk_attr_id = get_attr_id(packet_attr, ATTR_TYPE_ZDK)
                    red_all_charge = get_offer_inst_attr_val(son, user.wing_offer_inst_id, zdk_attr_id)
                    red_all_charge /= 100.0
                    # 取接口表中已经赠送的金额（包括所有状态）
                    red_pres_charge = son.query(func.nvl(func.sum(ARedPacket.red_charge), 0)).filter(
                        ARedPacket.red_id == user.red_id
                    ).scalar()
                    if red_pres_charge >= red_all_charge:
                        # 已经送完，不能再送了
                        user.finish_flag = FINISH_FLAG_TERMINAL
                        son_objects.append(user)
                        raise MyException(TerminalAmountOverflow())
                    elif red_pres_charge + red_amount >= red_all_charge:
                        # 最后一次赠送
                        red_charge = red_all_charge - red_pres_charge
                        user.finish_flag = FINISH_FLAG_TERMINAL
                        son_objects.append(user)
                    elif red_pres_charge == 0 and discount_flag == 0:
                        # 第一次送且需要计算折扣
                        red_charge = dis_value * red_amount
                    else:
                        red_charge = red_amount
                else:
                    # 有失效日期，抛异常
                    raise MyException(TerminalExpNotAllow())

            # 取区号
            org_area_code = get_area_code(son, sa.Serv.serv_id)
            area_name = None
            org_id = None
            if org_area_code is not None:
                area_name = areas_name_map.get(org_area_code).decode('utf-8').encode('gbk')
                org_id = areas_org_map.get(org_area_code)
            # 取欠费金额
            owe_charge = None
            if premise_flag == 1 or (premise_flag == 0 and premise_value is not None):
                # 对于有前提套餐或无前提套餐且套餐值不为空的规则，规则如下：
                # 1. 有前提套餐：判断出账费用是否小于套餐值
                # 2. 无前提套餐：判断出账费用是否小于固定值
                if premise_flag == 1 \
                        and (user.premise_eff_date is None or user.premise_exp_date is None):
                    raise MyException(MainEffExpNone())

                if action_type == ACTION_TYPE_FC:
                    owe_charge = get_aggr_charge(son, sa.ServAcct.acct_id, cycle.billing_cycle_id, org_id)
                else:
                    owe_charge = get_owe_charge(son, sa.ServAcct.acct_id, cycle.billing_cycle_id)

                # 红包套餐如果按日折算，主套餐也需要按日折算，然后判断月消费总金额是否大于套餐值
                if discount_flag == 0:
                    premise_value = round(dis_value * premise_value, 2)
                else:
                    premise_value = round(premise_value, 2)

                if 0 <= owe_charge < premise_value:
                    # 此处会将P0C和P0E的更新
                    state_flag = STATE_P0X

            if action_type == ACTION_TYPE_FC:
                if state_flag == STATE_P0P:
                    packet_p = ARedPacketPercent()
                    packet_p.red_id = user.red_id
                    packet_p.serv_id = user.serv_id
                    packet_p.billing_cycle_id = cycle.billing_cycle_id
                    packet_p.fix_charge = int(round(red_charge * 100, 0))
                    packet_p.org_id = org_id
                    packet_p.percent_type = 0

                    son_objects.append(packet_p)
            else:
                packet = ARedPacket()
                # 取用户信息插入接口表
                packet.cust_name = son.query(Cust).join(
                    Acct, Acct.cust_id == Cust.cust_id
                ).filter(
                    Acct.acct_id == sa.ServAcct.acct_id
                ).with_entities(Cust.cust_name).scalar()

                # 取序列
                packet_id = son.execute(select([Sequence('seq_red_packet_id').next_value()])).scalar()

                packet.red_id = user.red_id
                packet.packet_id = packet_id
                packet.area_name = area_name
                packet.main_offer_name = packet_rule.premise_offer_name
                packet.main_eff_date = user.premise_eff_date
                packet.main_charge = packet_rule.premise_plan_amount
                packet.red_offer_id = packet_rule.wing_offer_id
                packet.red_offer_name = packet_rule.wing_offer_name
                packet.red_eff_date = user.wing_eff_date
                packet.acc_nbr = sa.Serv.acc_nbr
                packet.reqnumtype = 1 if sa.Serv.billing_mode_id == 1 else 0
                packet.acct_month = month
                packet.red_charge = round(red_charge, 1)
                packet.state = state_flag
                packet.acct_id = sa.ServAcct.acct_id
                packet.bill_amount = owe_charge
                packet.action_type = action_type
                packet.discount_value = dis_value

                son_objects.append(packet)
            logging.info('serv_id=%ld,cycle=%d-->add' % (user.serv_id, cycle.billing_cycle_id))

            if state_flag == STATE_P0X:
                raise MyException(OweChargeLow())
            elif state_flag == STATE_P0C:
                '''
                # 判断欠费是否超达到3个月，达到3个月则更新永不赠送标识
                owe_month_num = son.query(func.count('*')).filter(
                    ARedPacket.red_id == user.red_id,
                    ARedPacket.state == STATE_P0C
                ).scalar()
                if owe_month_num >= 2:
                    user.finish_flag = FINISH_FLAG_OWE3MONTH
                    son_objects.append(user)
                '''
                # 此处不再对欠费三个月做判断，改到补送程序中判断
                raise MyException(OweNotCharge())
            elif state_flag == STATE_P0P:
                s_res = Success()
                s_res.msg = '赠送成功'
                raise MyException(s_res)
            elif state_flag == STATE_P0E:
                raise MyException(EarlierOfferExist())
            else:
                raise MyException(UnknownError())
        elif red_packet.state in (STATE_P0P, STATE_P0X, STATE_P0E):
            # 已经赠送过、出账金额低于套餐值或不是生效最早的套餐
            result = HasRecord()
        elif red_packet.state == STATE_P0C:
            # 接口表已经存在未赠送记录，判断是否需要更新状态
            # 判断用户是否欠费
            if owe_state == '10X':
                # 不欠费则更新状态
                red_packet.reqnumtype = 1 if sa.Serv.billing_mode_id == 1 else 0
                red_packet.state = STATE_P0P
                red_packet.state_date = func.now()
                red_packet.action_type = action_type
                son_objects.append(red_packet)
                packet_id = red_packet.packet_id

                logging.info('serv_id=%ld,cycle=%d-->update' % (user.serv_id, cycle.billing_cycle_id))
                raise MyException(RePresentSuccess())
            else:
                result = HasRecord()
        else:
            logging.error('red_packet.state not in (P0P,P0C,P0X)')
    except MyException, ex:
        # 处理结果插入结果表
        result = ex.value
        if action_type == ACTION_TYPE_FC:
            # 分成不插
            pass
        else:
            msg = result.msg.decode('utf-8').encode('gbk')
            acc_nbr = sa.Serv.acc_nbr if sa is not None else None

            packet_res = gene_result(son, acc_nbr, user.red_id, packet_id, month, result.code, msg)
            if packet_res is not None:
                son_objects.append(packet_res)
    except Exception, ex:
        result = SystemExcept()
        result.msg = ex.message
    finally:
        try:
            if result.code != SystemExcept().code and len(son_objects) > 0:
                son.add_all(son_objects)
                son.commit()
        except Exception, ex2:
            result = SystemExcept()
            result.msg = ex2.message
            son.rollback()

    return result


def present(son, red_id, month, action_type):
    try:
        if son is None:
            raise MyException(DBConnectNotFound())
        # 取账期
        billing_cycle_id = ''.join(['1', str(month)[2:]])
        cycle = son.query(BillingCycle).filter(
            BillingCycle.billing_cycle_id == billing_cycle_id
        ).first()

        if cycle is None:
            raise MyException(MonthInvalid())

        # 取需要送红包的用户
        packet_user = son.query(ARedPacketUser).filter(
            ARedPacketUser.finish_flag == FINISH_FLAG_NORMAL,
            ARedPacketUser.red_id == red_id
        ).first()

        if packet_user is not None:
            # 处理一个用户的红包
            result = deal(son, packet_user, cycle, action_type)
        else:
            raise MyException(RedUserNotFound())
    except MyException, ex:
        # 处理结果插入结果表
        result = ex.value
    except Exception, ex:
        result = SystemExcept()
        result.msg = ex.message
    finally:
        pass

    return result


class AsyncRedPacket(object):
    def __init__(self):
        self.async = AsyncModule()

    @auto_release
    def process(self, args):
        result = Success()
        son = self.async.session

        red_id = args.get('red_id')
        month = args.get('month')
        action_type = args.get('action_type')

        try:
            if red_id is None or month is None or action_type is None:
                result = ParameterNone()
            else:
                result = present(son, red_id, month, action_type)
        except Exception as ex:
            result = SystemExcept()
            result.msg = ex.message
        finally:
            if result is None:
                result = UnknownError()
                result.msg = 'result is None'

        return result.to_json()
