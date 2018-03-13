# -*- coding: UTF-8 -*-
from os import environ, getpid
import imp
from dict4ini import *
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from public_modules.models import *
from public_class.async_func import Singleton
from defines.variables import *

base_map = {
    'payment': 'PaymentBase',
    'bill': 'BillBase',
    'a_bill_owe': 'ABillOweBase',
    'acct_item_owe': 'AcctItemOweBase',
    'acct_item_aggr': 'AcctItemAggrBase',
}


class SplitTable(Singleton):
    def __init__(self):
        if not hasattr(self, '_table_conf'):
            self._table_conf = None

        if self._table_conf is None:
            self._table_conf = {
                'payment': dict(),
                'a_bill_owe': dict(),
                'acct_item_aggr': dict(),
                'acct_item_owe': dict(),
                'bill': dict(),
            }

    def get_table_conf(self, type_name):
        return self._table_conf.get(type_name)

    def set_table_conf(self, type_name, key, val):
        tb = self.get_table_conf(type_name)
        if tb.get(key) is None:
            tb[key] = val

    def gen_split_table(self, conf, base):
        """
        获取一个账期的对象
        :param conf:
        :param base:
        :return:
        """
        file_name = '%s_%s' % (base, getpid())
        for c in conf:
            with open('./public_modules/%s.py' % file_name, 'w') as f:
                base_name = base_map.get(base)
                file_list = list()
                file_list.append('# -*- coding: UTF-8 -*-\n')
                file_list.append('from models import %s\n\n\n' % base_name)
                file_list.append('class %s(%s): pass\n\n\n' % (str(c.table_name).upper(), base_name))
                f.writelines(file_list)
                f.flush()

            module_name = ''.join(['public_modules.', file_name])
            table_name = str(c.table_name).upper()
            m = __import__(module_name, globals(), locals(), [table_name], -1)
            if len(self._table_conf.get(base)) > 0:
                print table_name
                imp.reload(m)

            return getattr(m, table_name)

    def get_table_cls(self, son, cycle_id, org_id, type_name):
        """
        取分表类，不存在则新建
        :param son:
        :param cycle_id:
        :param org_id:
        :param type_name:
        :return:
        """
        if type_name == TB_NAME_AGGR:
            key = ''.join([str(cycle_id), '_', str(org_id)])
        else:
            key = str(200000 + int(cycle_id) - 10000)
        '''
        if type_name == TB_NAME_AGGR:
            key = ''.join(['20', str(cycle_id)[1:], '_', str(org_id)])
        else:
            key = ''.join(['20', str(cycle_id)[1:]])
        '''

        map_conf = self.get_table_conf(type_name)
        cls = map_conf.get(key)

        if cls is None:
            if type_name == TB_NAME_AGGR:
                split_conf = get_bill_split_table(son, [cycle_id], SPLIT_TABLE_TYPE_MAP.get(type_name), [org_id])
            else:
                split_conf = get_acct_split_table(son, [cycle_id], SPLIT_TABLE_TYPE_MAP.get(type_name))
            cls = self.gen_split_table(split_conf, type_name)
            self.set_table_conf(type_name, key, cls)

        return cls


def get_acct_split_table(son, cycles, tb_type):
    """
    取账务侧分表
    :param son:
    :param cycles:
    :param tb_type:
    :return:
    """
    return son.query(ASplitTableConfig).filter(
        ASplitTableConfig.billing_cycle_id.in_(cycles),
        ASplitTableConfig.table_type == tb_type,
    ).all()


def get_bill_split_table(son, cycles,tb_type, orgs):
    """
    取计费侧分表
    :param son:
    :param cycles:
    :param tb_type:
    :param orgs:
    :return:
    """
    return son.query(BInstTableList).filter(
        BInstTableList.billing_cycle_id.in_(cycles),
        BInstTableList.table_type == tb_type,
        BInstTableList.org_id.in_(orgs),
        BInstTableList.billflow_id.is_(None),
    ).order_by(BInstTableList.billing_cycle_id.asc(), BInstTableList.org_id).all()


def gen_split_tables_all(conf, base):
    with open('./public_modules/%s.py' % base, 'w') as f:
        base_name = base_map.get(base)
        file_list = list()
        file_list.append('# -*- coding: UTF-8 -*-\n')
        file_list.append('from models import %s\n\n\n' % base_name)

        ts = []
        for c in conf:
            t = 'class %s(%s): pass\n\n\n' % (str(c.table_name).upper(), base_name)
            if t not in ts:
                file_list.append(t)
                ts.append(t)

        file_list.append('TB_%s = {\n' % str(base).upper())
        blank = '    '
        for c in conf:
            if base == 'acct_item_aggr':
                key = ''.join([str(c.billing_cycle_id), '_', str(c.org_id)])
            else:
                key = str(200000 + c.billing_cycle_id - 10000)
            file_list.append(''.join([
                blank, '\'', key, '\': ', str(c.table_name).upper(), ',\n'
            ]))

        file_list.append('}\n')
        f.writelines(file_list)


def gen_tables_all(son):

    billing_cycles = son.query(BillingCycle.billing_cycle_id).filter(
        BillingCycle.cycle_begin_date.between(
            func.to_date('201401', 'yyyymm'),
            func.to_date('201912', 'yyyymm')
        ),
    ).all()

    cycles = []
    for c in billing_cycles:
        cycles.append(c.billing_cycle_id)

    orgs = []
    for org in areas_org_map.itervalues():
        orgs.append(org)

    split_conf = get_acct_split_table(son, cycles, TB_TYPE_PAYMENT)
    gen_split_tables_all(split_conf, 'payment')
    split_conf = get_acct_split_table(son, cycles, TB_TYPE_BILL)
    gen_split_tables_all(split_conf, 'bill')
    split_conf = get_acct_split_table(son, cycles, TB_TYPE_BILL_OWE)
    gen_split_tables_all(split_conf, 'a_bill_owe')
    split_conf = get_acct_split_table(son, cycles, TB_TYPE_OWE)
    gen_split_tables_all(split_conf, 'acct_item_owe')

    split_conf = get_bill_split_table(son, cycles, TB_TYPE_AGGR, orgs)
    gen_split_tables_all(split_conf, 'acct_item_aggr')


if __name__ == '__main__':
    secretKey = environ.get('LINKAGE_KEY')
    config = dict4ini.DictIni('access_config.ini', secretKey=secretKey).dict()
    db_conf = config.get('DB_ORACLE').get('ACCT_T5')
    conn_str = ''.join([
        'oracle://',
        db_conf['user'], ':',
        db_conf['password'], '@',
        db_conf['tns']
    ])
    engine = sqlalchemy.create_engine(conn_str, encoding='gbk', echo=False)
    Session = sessionmaker(bind=engine)
    son = Session()
    gen_tables_all(son)
