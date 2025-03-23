from functools import partial
import pytest
import uuid

from sanic import Sanic
from sqlalchemy import func, select

from app.models.bill import Bill, Transactions
from app.models.users import User
from app.utils import get_signature

LOGIN_API_URL = 'api_auth_bp.login'
REFRESH_API_URL = 'api_auth_bp.refresh'
USER_API_URL = 'api_user_bp.users_list'
ME_API_URL = 'api_user_bp.user_me'
PAY_WH_URL = 'wh_pay_bp.wh_pay'
TS_API_URL = 'wh_pay_bp.bills_info'



def get_transaction_data(
        app: Sanic,
        amount: float,
        account_id: int,
        user_id: int,
        transaction_id: str = None,
    ):
        if not transaction_id:
            transaction_id = str(uuid.uuid4())

        ts_d = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "account_id": account_id,
            "amount": amount,
        }
        secret_key = app.config.SECRET_KEY
        sign = get_signature(
            f"{ts_d['account_id']}{ts_d['amount']}{ts_d['transaction_id']}{ts_d['user_id']}{secret_key}"
        )
        ts_d['signature'] = sign
        return ts_d
    
async def check_bill_transactions_cnt(async_db_session, bill_exp_cnt: int, ts_exp_cnt: int):
    transaction_cnt = (await async_db_session.execute(func.count(Transactions.id))).scalar()
    bill_cnt = (await async_db_session.execute(func.count(Bill.id))).scalar()
    assert bill_cnt == bill_exp_cnt
    assert transaction_cnt == ts_exp_cnt

async def check_bill_model(async_db_session, account_id, exp_amount):
    new_bill = (await async_db_session.execute(
        select(Bill)
        .where(Bill.account_id == account_id)
    )).scalars().first()
    assert new_bill, 'Bill not created!'
    assert float(new_bill.amount) == exp_amount, f'{new_bill.amount} != {exp_amount}'
    return new_bill

async def check_ts_model(async_db_session, transaction_id, exp_amount, bill_id):
    transaction = (await async_db_session.execute(
        select(Transactions)
        .where(
            Transactions.transaction_id == transaction_id,
            Transactions.bill_id == bill_id
            )
    )).scalars().first()
    assert transaction, 'Transactions not created!'
    assert float(transaction.t_amount) == exp_amount
    return transaction
    
async def check_user(
    async_session, 
    user_id, 
    deleted_exp: bool = False,
    name_exp: str = None, 
    email_exp: str = None,
    ):
    user = (await async_session.execute(
        select(User)
        .where(User.id == user_id)
    )).scalars().first()

    if deleted_exp:
        assert not user, 'User Not Deleted!'
        return
    assert user.email == email_exp
    assert user.name == name_exp