# -*- coding:utf8 -*-
import logging

STATE_P0P = 'P0P'
STATE_P0C = 'P0C'
STATE_P0X = 'P0X'
STATE_P0E = 'P0E'
OWE_STATE_10A = '10A'
OWE_STATE_10X = '10X'
OWE_STATE_10C = '10C'
OWE_5JA = '5JA'
OWE_5JB = '5JB'
OWE_5JC = '5JC'
PAYMENT_OPER_5KA = '5KA'
PAYMENT_OPER_5KB = '5KB'
PAYMENT_OPER_5KE = '5KE'
PAYMENT_STATE_C0C = 'C0C'
PAYMENT_STATE_C0R = 'C0R'
BILL_STATE_40C = '40C'
BILL_STATE_40R = '40R'
MODIFY_STATE_P0C = 'P0C'
MODIFY_STATE_P0P = 'P0P'
MODIFY_STATE_P0E = 'P0E'
MODIFY_STATE_P0X = 'P0X'
# MIN_CHARGE_ATTR_ID = 509224
MIN_BILLING_CYCLE = 11612
FINISH_FLAG_NORMAL = 0
FINISH_FLAG_EXPIRE = 1
FINISH_FLAG_OWE3MONTH = 2
FINISH_FLAG_OFF_LINE = 4
FINISH_FLAG_TERMINAL = 5
LIMIT_MONTH = 3
PROCESS_NUM = 2
ACTION_TYPE_ALL = 0
ACTION_TYPE_ADD = 1
ACTION_TYPE_BS = 2
ACTION_TYPE_FC = 3

# ATTR_TYPE: 0-终端款，1-保底值，2-赠送金额
ATTR_TYPE_ZDK = 1
ATTR_TYPE_BD = 2
ATTR_TYPE_ZSJE = 3

# 分表相关
TB_TYPE_OWE = 1
TB_TYPE_PAYMENT = 2
TB_TYPE_BILL = 3
TB_TYPE_BILL_OWE = 4
TB_TYPE_AGGR = 11

'''
TB_PAYMENT = {}
TB_BILL_OWE = {}
TB_ACCT_ITEM_AGGR = {}
TB_ACCT_ITEM_OWE = {}
TB_BILL = {}
'''
TB_NAME_PAYMENT = 'payment'
TB_NAME_BILL_OWE = 'a_bill_owe'
TB_NAME_AGGR = 'acct_item_aggr'
TB_NAME_OWE = 'acct_item_owe'
TB_NAME_BILL = 'bill'

SPLIT_TABLE_CONF_MAP = {
    'payment': dict(),
    'a_bill_owe': dict(),
    'acct_item_aggr': dict(),
    'acct_item_owe': dict(),
    'bill': dict(),
}

SPLIT_TABLE_TYPE_MAP = {
    'payment': TB_TYPE_PAYMENT,
    'a_bill_owe': TB_TYPE_BILL_OWE,
    'acct_item_aggr': TB_TYPE_AGGR,
    'acct_item_owe': TB_TYPE_OWE,
    'bill': TB_TYPE_BILL,
}

areas_name_map = {
    '0691': '版纳',
    '0692': '德宏',
    '0870': '昭通',
    '0871': '昆明',
    '0872': '大理',
    '0873': '红河',
    '0874': '曲靖',
    '0875': '保山',
    '0876': '文山',
    '0877': '玉溪',
    '0878': '楚雄',
    '0879': '普洱',
    '0883': '临沧',
    '0886': '怒江',
    '0887': '迪庆',
    '0888': '丽江',
}

areas_org_map = {
    '0691': 691,
    '0692': 692,
    '0870': 870,
    '0871': 2,
    '0872': 872,
    '0873': 873,
    '0874': 874,
    '0875': 875,
    '0876': 876,
    '0877': 877,
    '0878': 878,
    '0879': 879,
    '0883': 883,
    '0886': 886,
    '0887': 887,
    '0888': 888,
}

# 开关
EOP_ALIPAY_SWITCH_ID = 717520020
