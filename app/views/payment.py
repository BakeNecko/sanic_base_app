import hashlib
from http.client import HTTPException

from sanic import Blueprint, BadRequest, Sanic, NotFound, json
from sanic_ext import validate
from sqlalchemy import and_, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.bill import Transactions, Bill
from app.models import User, Transactions
from app.permissions import login_required
from app.serializers import BillSerializer, ExternalPayWH
from app.utils import get_limit_offset_params, get_signature


wh_pay_bp = Blueprint("wh_pay_bp", url_prefix="/wh/")

app = Sanic.get_app()


@wh_pay_bp.post("/", name='wh_pay')
@validate(ExternalPayWH)
# @login_required ???
async def wh_external_pay(request, body: ExternalPayWH):
    """
    Получили WebHook от сторон. плат. сист. 
    transaction_id:
    account_id: уникальный идентификатор счета пользователя (model.Bill)
    user_id: уникальный идентификатор счета пользователя / Всм ID  пользователя? (model.User)
    amount:
    signature: must be eq
    SHA256-HASH(
        {account_id}{amount}{transaction_id}{user_id}{secret_key} 
        +
        app.config.SECRET_KEY
    )

    """
    signature_string = f"{body.account_id}{body.amount}{body.transaction_id}{body.user_id}{app.config.SECRET_KEY}"

    calculated_signature = get_signature(signature_string)
    try:
        if calculated_signature != body.signature:
            raise BadRequest('check signature eq is fkp')

        async with request.ctx.session as session:
            user = (await session.execute((
                select(User)
                .filter(User.id == body.user_id,)
            ))).scalars().first()
            if not user:
                raise NotFound('User not found')

            bill = (await session.execute(select(Bill).where(
                Bill.account_id == body.account_id,
                Bill.user_id == user.id,
            ))).scalars().first()
            if not bill:
                # check amount >= 0 ?
                bill = Bill(
                    user_id=user.id,
                    amount=body.amount,
                    account_id=body.account_id,
                )
                session.add(bill)
            else:
                bill.amount += body.amount

            session.add(Transactions(
                transaction_id=body.transaction_id,
                t_amount=body.amount,
                bill=bill,
            ))
            await session.commit()

        return json({"message": "Webhook received successfully"}, status=200)
    except IntegrityError as e:
        raise BadRequest('transaction_id already registered!')
    except HTTPException as e:
        raise e


@wh_pay_bp.get("/bills", name='bills_info')
@login_required
async def bills_info(request):
    limit, offset = get_limit_offset_params(request.args)
    smtp = (
        select(Bill)
        .options(selectinload(Bill.transactions))
        .limit(limit)
        .offset(offset)
    )

    if not request.ctx.is_admin:
        smtp = smtp.where(Bill.user_id == request.ctx.user_id)
    bills = (await request.ctx.session.execute(smtp)).scalars().all()
    return json([BillSerializer.model_validate(bill).model_dump() for bill in bills])


@wh_pay_bp.get("/bills/<bill_id:int>", name='bill_detail')
@login_required
async def bill_detail(request, bill_id=None):
    q_filter = (Bill.id == bill_id)
    if not request.ctx.is_admin:
        q_filter = (and_(Bill.id == bill_id, Bill.user_id == request.ctx.user_id))

    smtp = (
        select(Bill)
        .options(selectinload(Bill.transactions))
        .where(q_filter)
        .order_by(desc(Bill.created_at))
    )
    bill = (await request.ctx.session.execute(smtp)).scalars().first()
    if not bill:
        raise NotFound('Bill not found or you do not have access')
    return json(BillSerializer.model_validate(bill).model_dump(), status=200)
