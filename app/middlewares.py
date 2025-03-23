import jwt
from sqlalchemy.orm import sessionmaker
from sanic import Sanic, Unauthorized
from contextvars import ContextVar
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.users import User

app = Sanic.get_app()

engine = create_async_engine(
    f"postgresql+asyncpg://{app.config.POSTGRES_USER}:{app.config.POSTGRES_PASSWORD}@{app.config.POSTGRES_HOST}/{app.config.POSTGRES_DB}", 
    echo=True,
    )

_sessionmaker = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    )

_base_model_session_ctx = ContextVar("session", default=None)
        

def setup_middleware(app):
    @app.middleware("request", priority=1)
    async def add_user_to_request(request):
        token = request.headers.get("Authorization")
        request.ctx.user_id = None
        request.ctx.is_admin = None

        if token:
            token = token.split()
            if len(token) > 1:
                token = token[1] # Bearer
            else:
                token = token[0]
            try:
                payload = jwt.decode(
                    token, 
                    app.config.SECRET_KEY, 
                    algorithms='HS256',
                    )
                # safer
                user = await request.ctx.session.get(User, payload['id'])
                request.ctx.user_id = user.id
                request.ctx.is_admin = user.is_admin
            except jwt.ExpiredSignatureError:
                raise Unauthorized('Token has expired')
            except jwt.PyJWTError as e:
                raise Unauthorized(f'Token invalid | e: {e}')
        
                
    @app.middleware("request", priority=2)
    async def inject_session(request):
        session = _base_model_session_ctx.get()
        
        if not session:
            session = _sessionmaker()
        request.ctx.session = session
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)

    @app.middleware("response", priority=2)
    async def close_session(request, response):
        if hasattr(request.ctx, "session_ctx_token"):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()
