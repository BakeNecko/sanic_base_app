from functools import partial
from deepdiff import DeepDiff
import pytest
import uuid

from sqlalchemy import func, select

from app.models.bill import Bill, Transactions
from app.models.users import User
from .utils import (
    USER_API_URL,
    ME_API_URL,
    PAY_WH_URL,
    check_bill_model,
    check_bill_transactions_cnt,
    check_ts_model,
    check_user,
    get_transaction_data,
)
from app.utils import get_signature


@pytest.mark.asyncio
async def test_get_users_list(
    get_jwt_admin_access,
    get_jwt_access,
    app,
):
    url = app.url_for(USER_API_URL)

    header_admin = {'Authorization': f'Bearer {get_jwt_admin_access}'}
    header_normal = {'Authorization': f'Bearer {get_jwt_access}'}

    # Admin Get Users-List
    _, response = await app.asgi_client.get(url, headers=header_admin)
    assert response.status == 200  #
    assert isinstance(response.json, list)
    assert len(response.json) > 2, 'body assert failed'

    # Normal User Get Users-List - expect Permission Error
    _, response = await app.asgi_client.get(url, headers=header_normal)
    assert response.status == 403


@pytest.mark.asyncio
async def test_put_users_list(
    async_db_session,
    get_jwt_admin_access,
    get_jwt_access,
    user_normal,
    app,
):
    url = app.url_for(USER_API_URL)

    header_admin = {'Authorization': f'Bearer {get_jwt_admin_access}'}
    header_normal = {'Authorization': f'Bearer {get_jwt_access}'}
    new_email = 'new_email@mail.ru'
    new_name = 'new_name'
    body = {
        'user_ids': [user_normal.id],
        'email': new_email,
        'name': new_name,
    }
    # Admin Get Users-List
    _, response = await app.asgi_client.put(url, headers=header_admin, json=body)
    assert response.status == 200  #
    await check_user(
        async_db_session,
        user_normal.id,
        email_exp=new_email,
        name_exp=new_name,
    )

    # Normal User Put Users-List - expect Permission Error
    _, response = await app.asgi_client.get(url, headers=header_normal)
    assert response.status == 403


@pytest.mark.asyncio
async def test_create_user(
    async_db_session,
    get_jwt_admin_access,
    get_jwt_access,
    app,
):
    url = app.url_for(USER_API_URL)

    header_admin = {'Authorization': f'Bearer {get_jwt_admin_access}'}
    header_normal = {'Authorization': f'Bearer {get_jwt_access}'}
    body = {
        'name': 'New',
        'email': 'new@mail.ru',
        'password': '1234',
        'is_admin': True,
    }
    # Admin Create User
    _, response = await app.asgi_client.post(url, headers=header_admin, json=body)
    assert response.status == 201  #
    await check_user(
        async_db_session,
        response.json.get('id'),
        email_exp=body['email'],
        name_exp=body['name'],
    )

    # Normal User Create user - expect Permission Error
    _, response = await app.asgi_client.post(url, headers=header_normal, json=body)
    assert response.status == 403


@pytest.mark.asyncio
async def test_delete_users_list(
    async_db_session,
    get_jwt_admin_access,
    get_jwt_access,
    many_users,
    app,
):
    url = app.url_for(USER_API_URL)

    header_admin = {'Authorization': f'Bearer {get_jwt_admin_access}'}
    header_normal = {'Authorization': f'Bearer {get_jwt_access}'}
    params = {
        'user_ids': many_users,
    }
    # Admin Delete Users-List
    _, response = await app.asgi_client.delete(url, headers=header_admin, params=params)
    assert response.status == 204  #

    for u_id in many_users:
        await check_user(async_db_session, user_id=u_id, deleted_exp=True)

    # Normal User Delete Users-List - expect Permission Error
    _, response = await app.asgi_client.delete(url, headers=header_normal, params=params)
    assert response.status == 403


@pytest.mark.asyncio
async def test_me_info(
    app,
    get_jwt_access,
):
    header_normal = {'Authorization': f'Bearer {get_jwt_access}'}
    url = app.url_for(ME_API_URL)
    _, response = await app.asgi_client.get(url, headers=header_normal)
    assert response.status == 200


@pytest.mark.asyncio
async def test_pay_wh(
    async_db_session,
    get_jwt_access,
    user_normal,
    app,
):
    header_user = {'Authorization': f'Bearer {get_jwt_access}'}

    url = app.url_for(PAY_WH_URL)

    account_id = 10101
    amount = 100.55
    ts_d = get_transaction_data(
        app=app,
        amount=amount,
        account_id=account_id,
        user_id=user_normal.id,
    )
    transaction_id = ts_d['transaction_id']

    # Pay
    _, response = await app.asgi_client.post(url, headers=header_user, json=ts_d)
    assert response.status == 200

    # Check models
    await check_bill_transactions_cnt(async_db_session, 1, 1)
    bill = await check_bill_model(async_db_session, account_id, amount)
    await check_ts_model(async_db_session, transaction_id, amount, bill.id)

    # Try pay with same transaction_id - UniqueError expected
    _, response = await app.asgi_client.post(url, headers=header_user, json=ts_d)
    assert response.status == 400
    assert response.json['message'] == 'transaction_id already registered!'

    # Nothig change
    await check_bill_transactions_cnt(async_db_session, 1, 1)
    bill = await check_bill_model(async_db_session, account_id, amount)
    await check_ts_model(async_db_session, transaction_id, amount, bill.id)

    # Another pay with another transaction_id
    exp_amount = amount + 0.45
    amount = 0.45
    ts_d = get_transaction_data(
        app=app,
        amount=amount,
        account_id=account_id,
        user_id=user_normal.id,
    )
    transaction_id = ts_d['transaction_id']

    # Pay
    _, response = await app.asgi_client.post(url, headers=header_user, json=ts_d)
    assert response.status == 200

    await check_bill_transactions_cnt(async_db_session, 1, 2)
    bill = await check_bill_model(async_db_session, account_id, exp_amount)
    await check_ts_model(async_db_session, transaction_id, amount, bill.id)

    # Negative Pay
    neg_amount = -100
    exp_amount = exp_amount + neg_amount
    ts_d = get_transaction_data(
        app=app,
        amount=neg_amount,
        account_id=account_id,
        user_id=user_normal.id,
    )
    transaction_id = ts_d['transaction_id']
    _, response = await app.asgi_client.post(url, headers=header_user, json=ts_d)
    assert response.status == 200

    await check_bill_transactions_cnt(async_db_session, 1, 3)
    bill = await check_bill_model(async_db_session, account_id, exp_amount)
    await check_ts_model(async_db_session, transaction_id, neg_amount, bill.id)

    # Check signature verification
    ts_d = get_transaction_data(
        app=app,
        amount=neg_amount,
        account_id=account_id,
        user_id=user_normal.id,
    )
    ts_d['signature'] = str(uuid.uuid4())
    _, response = await app.asgi_client.post(url, headers=header_user, json=ts_d)
    assert response.status == 400, response.json
    assert response.json['message'] == 'check signature eq is fkp'

    # Final, get info about new Bill
    url = app.url_for(ME_API_URL)
    _, response = await app.asgi_client.get(url, headers=header_user)
    assert response.status == 200
    diff = DeepDiff(
        response.json['bills'],
        [{
            'id': bill.id,
            'account_id': account_id,
            'amount': float(exp_amount),
            'user_id': user_normal.id,
        }], ignore_order=True)
    assert not diff


@pytest.mark.asyncio
async def test_get_ts_info(
    async_db_session,
    get_jwt_access,
    get_jwt_admin_access,
    user_normal,
    get_bills_with_ts,
    get_user_normal_bill,
    app,
):
    # User get all his bills
    headers = {'Authorization': f'Bearer {get_jwt_access}'}
    headers_admin = {'Authorization': f'Bearer {get_jwt_admin_access}'}
    url = app.url_for('wh_pay_bp.bills_info')

    _, response = await app.asgi_client.get(url, headers=headers)
    assert response.status == 200
    assert len(response.json) == len(get_user_normal_bill)

    # User get his specific Bill
    specific_bill_id = get_user_normal_bill[-1].id
    url_by_id = app.url_for('wh_pay_bp.bill_detail', bill_id=specific_bill_id)
    _, response = await app.asgi_client.get(url_by_id, headers=headers_admin)
    assert response.status == 200
    assert response.json['id'] == specific_bill_id
    assert response.json['account_id'] == get_user_normal_bill[-1].account_id

    # Admin get ALL Bills
    _, response = await app.asgi_client.get(url, headers=headers_admin)
    assert response.status == 200
    assert len(response.json) == len(get_bills_with_ts) + len(get_user_normal_bill)
