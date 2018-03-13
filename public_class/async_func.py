# -*- coding:utf8 -*-
from os import environ
from os.path import abspath, dirname, join
import logging
from dict4ini import *
import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from functools import wraps

secret_key = environ.get('LINKAGE_KEY')
access_path = join(dirname(abspath(__file__)), '../access_config.ini')
config = dict4ini.DictIni(access_path, secretKey=secret_key).dict()
# db_conf = config.get('DB_ORACLE').get('235')
db_conf = config.get('DB_ORACLE').get('ACCT_T5')
conn_str = ''.join([
    'oracle://',
    db_conf['user'], ':',
    db_conf['password'], '@',
    db_conf['tns']
])


def auto_release(func):
    """
    修饰器
    :param func:
    :return:
    """
    @wraps(func)
    def release(self, args):
        try:
            task = func(self, args)
        except Exception as ex:
            task = None
            logging.error(ex.message)
        finally:
            self.async.release()
        return task
    return release


class Singleton(object):
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls)
        return cls._instance


class AsyncModule(Singleton):
    def __init__(self):
        if not hasattr(self, '_session_factory'):
            self._session_factory = None

        if self._session_factory is None:
            engine = sqlalchemy.create_engine(
                conn_str, encoding='gbk', echo=False,
                pool_recycle=1800, pool_timeout=30
            )
            self._session_factory = scoped_session(sessionmaker(bind=engine))

    @property
    def session(self):
        return self._session_factory()

    def release(self):
        self._session_factory.remove()
