import bcrypt
import jwt
from sanic import BadRequest, Blueprint, Sanic, json, NotFound
from sanic_ext import validate
from sqlalchemy import select

from app.models.users import User
from app.serializers import LoginRequest
from app.utils import timezone_now

api_auth_bp = Blueprint("api_auth_bp", url_prefix="/auth/")

app = Sanic.get_app()

@api_auth_bp.post("/login", name='login')
@validate(LoginRequest)
async def login_view(request, body: LoginRequest):
    """Log View handler
    Совпали пароли -> получили 2а токена.
    access - для промежуточных запросов. 
    refresh - для получения новго access токена. 
    ---
    Храним refresh токен в Redis с временем хранения равным exp.
    Чтобы сделать logout пользователя удаляем токен из Redis ->
    соотв. @login_required не подтвердит наличие токена и 
    пользователь будет деавторизован.
    """
    async with request.ctx.session as session:
        result = await session.execute(select(User).where(User.email == body.email))
        user = result.scalars().first()
        if not user:
            raise NotFound('User not found')

        if bcrypt.checkpw(body.password.encode('utf-8'), user.password.encode('utf-8')):

            access_token = jwt.encode({
                'id': user.id,
                'is_admin': user.is_admin,
                'exp': timezone_now() + app.config.ACCESS_TOKEN_EXPIRE_DELTA
            }, app.config.SECRET_KEY, algorithm=app.config.ALGO)

            refresh_token = jwt.encode({
                'id': user.id,
                'exp': timezone_now() + app.config.REFRESH_TOKEN_EXPIRE_DELTA
            }, app.config.SECRET_KEY, algorithm=app.config.ALGO)

            return json({
                'access_token': access_token,
                'refresh_token': refresh_token
            })
        raise BadRequest('Invalid password')
        
@api_auth_bp.post('/refresh', name='refresh')
async def refresh(request):
    refresh_token = request.json.get('refresh_token')
    
    try:
        payload = jwt.decode(
            refresh_token, 
            app.config.SECRET_KEY, 
            algorithms=app.config.ALGO,
            )
        user_id = payload['id']
    except jwt.ExpiredSignatureError:
        return json({'error': 'Refresh token expired'}, status=401)
    except jwt.InvalidTokenError:
        return json({'error': 'Invalid refresh token'}, status=401)

    async with request.ctx.session as session:
        user = await session.get(User, user_id)
        if not user:
            return json({'error': 'User  not found'}, status=404)
        
        # Генерация нового access token
        new_access_token = jwt.encode(
            {'id': user.id,
             'is_admin': user.is_admin,
             'exp': timezone_now() + app.config.ACCESS_TOKEN_EXPIRE_DELTA,
             }, 
            app.config.SECRET_KEY, 
            algorithm=app.config.ALGO, 
            )
        
        return json({'access_token': new_access_token})
