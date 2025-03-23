import hashlib
import hmac
from sanic import Blueprint, json, Request, Sanic, NotFound
from sanic.views import HTTPMethodView
from sanic_ext import validate
from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from app.permissions import login_required, is_admin_permission
from app.models import User
from app.serializers import (
    CreateUserReqeuest,
    UpdateUserRequest, 
    UpdateUsersList, 
    UserBaseRetrieve, 
    UserRetrieve,
)
from app.utils import get_limit_offset_params, hash_password

api_user_bp = Blueprint("api_user_bp", url_prefix="/users/")

app = Sanic.get_app()

class UserListView(HTTPMethodView):
    decorators = [login_required, is_admin_permission]
    
    async def get(self, request: Request):
        limit, offset = get_limit_offset_params(request.args)
        
        async with request.ctx.session as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.bills))
                .limit(limit)
                .offset(offset)
                )
            users = result.scalars().all()
            return json([UserRetrieve.model_validate(user).model_dump() for user in users])

        
    @validate(json=CreateUserReqeuest)
    async def post(self, request, body: CreateUserReqeuest):
        session = request.ctx.session
        body.password = hash_password(body.password)
        
        async with session.begin():
            new_user = User(**body.model_dump())
            session.add(new_user)
        await session.commit()
        return json(UserBaseRetrieve.model_validate(new_user).model_dump(), status=201)

    @validate(json=UpdateUsersList)
    async def put(self, request, body: UpdateUsersList):
        data = body.model_dump(exclude_unset=True)
        user_ids = data.pop('user_ids')

        async with request.ctx.session as session:
            stmt = (
                update(User)
                .where(User.id.in_(user_ids))
                .values(**data)
                .returning(User)
            )
            result = await session.execute(stmt)
            updated_users = result.scalars()
            await session.commit()
            return json([UserBaseRetrieve.model_validate(user).model_dump() for user in updated_users])

    async def delete(self, request):
        user_ids = request.args.getlist('user_ids', None)
        if not user_ids:
            raise NotFound('specify the Users to be deleted')
        user_ids = [int(u_id) for u_id in user_ids]
        async with request.ctx.session as session:
            stmt = delete(User).where(User.id.in_(user_ids))
            await session.execute(stmt)
            await session.commit()
        return json({"detail": "Users deleted successfully"}, status=204)
        
        
class UserRetrieveView(HTTPMethodView):
    decorators = [login_required]
    
    async def get(self, request):
        user_id = request.ctx.user_id
        async with request.ctx.session as session:
            # user = await session.get(User, user_id).options(selectinload(User.bills))
            user = (
                await session.execute(
                    select(User)
                    .options(selectinload(User.bills))
                    .where(User.id == user_id))
                ).scalars().first()

        return json(UserRetrieve.model_validate(user).model_dump())
    
    @validate(UpdateUserRequest)
    async def put(self, request, body: UpdateUserRequest):
        user_id = request.ctx.user_id
        data = body.model_dump(exclude_unset=True)
        
        async with request.ctx.session as session:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(**data)
                .returning(User)
            )
            result = (await session.execute(stmt)).scalars().first()
            await session.commit()
        return json(UserBaseRetrieve.model_validate(result).model_dump())

api_user_bp.add_route(UserListView.as_view(), '/', name='users_list')
api_user_bp.add_route(UserRetrieveView.as_view(), '/me', name='user_me')
    