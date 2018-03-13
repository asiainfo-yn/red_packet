# -*- coding: UTF-8 -*-
from public_modules.models import *


class AAgentTrustLog(Base):
    __tablename__ = 'a_agent_trust_log'

    acct_id = Column(Integer, primary_key=True)
    payment_id = Column(Integer)
    amount = Column(Integer)
    billing_cycle_id = Column(Integer, primary_key=True)
    create_date = Column(DateTime, default=func.now())
    state = Column(String(3))
    oper_type = Column(Integer)
    bill_result = Column(String(64))
    pay_result = Column(String(64))
    request_no = Column(String(32))
