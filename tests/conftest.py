from contextvars import ContextVar
import re
from typing import Any
import jwt
import pytest
import pytest_asyncio
from sanic.touchup.service import TouchUp

from sanic import Sanic
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import PytestConfig
from app.models.base import Base
from app.server import create_app
from .factories import TransactionFactory, UserFactory
from app.utils import timezone_now, hash_password


# https://github.com/sanic-org/sanic/blob/main/tests/conftest.py
slugify = re.compile(r"[^a-zA-Z0-9_\-]")
CACHE: dict[str, Any] = {}


@pytest_asyncio.fixture
async def async_db_session(monkeypatch, app):
    """The expectation with async_sessions is that the
    transactions be called on the connection object instead of the
    session object. 
    Detailed explanation of async transactional tests
    <https://github.com/sqlalchemy/sqlalchemy/issues/5811>
    """
    _sessionmaker = sessionmaker(
        app.ctx.async_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
        class_=AsyncSession,
    )
    connection = await app.ctx.async_engine.connect()
    trans = await connection.begin()
    async_session = _sessionmaker(bind=connection)
    nested = await connection.begin_nested()

    @event.listens_for(async_session.sync_session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested

        if not nested.is_active:
            nested = connection.sync_connection.begin_nested()
    
    # Base.metadata.create_all(app.ctx.sync_engine)
    await connection.run_sync(Base.metadata.create_all)
    monkeypatch.setattr('app.middlewares._base_model_session_ctx', ContextVar('session', default=async_session))

    yield async_session
    await connection.run_sync(Base.metadata.drop_all)
    # Base.metadata.drop_all(app.ctx.sync_engine)
    await trans.rollback()
    await async_session.close()
    await connection.close()

@pytest_asyncio.fixture
async def app(request):
    if not CACHE:
        for target, method_name in TouchUp._registry:
            CACHE[method_name] = getattr(target, method_name)
    
    app = create_app(slugify.sub("-", request.node.name))
    app.config.update_config(PytestConfig)
    
    connection_str = f"postgresql+asyncpg://{app.config.POSTGRES_USER}:{app.config.POSTGRES_PASSWORD}@{app.config.POSTGRES_HOST}/{app.config.POSTGRES_DB}"
    app.ctx.async_engine = create_async_engine(
        connection_str, 
        pool_size=10, echo=True, max_overflow=10
        )

    yield app
    for target, method_name in TouchUp._registry:
        setattr(target, method_name, CACHE[method_name])
    Sanic._app_registry.clear()


@pytest.fixture
def default_password():
    return 'default_password'

@pytest_asyncio.fixture(autouse=True)
async def user_admin(async_db_session, default_password):
    user = UserFactory(
        session=async_db_session,
        email='admin@mail.ru',
        password=default_password,
        is_admin=True, 
        )
    await async_db_session.commit()
    return user


@pytest_asyncio.fixture(autouse=True)
async def user_normal(async_db_session, default_password):
    user = UserFactory(
        session=async_db_session,
        email='user@mail.ru',
        password=default_password,
        is_admin=False, 
        )
    await async_db_session.commit()
    return user

@pytest_asyncio.fixture(autouse=True)
async def many_users(async_db_session) -> list[int]:
    users = UserFactory.create_batch(
            5,
            session=async_db_session,
            password='1234',
            is_admin=False, 
    )
    await async_db_session.commit()
    return [u.id for u in users]

def get_jwt_for_user(user, app, expired: bool = False) -> str:
    exp = timezone_now() + app.config.ACCESS_TOKEN_EXPIRE_DELTA
    if expired:
        exp -= app.config.ACCESS_TOKEN_EXPIRE_DELTA * 2
    return jwt.encode({
        'id': user.id,
        'exp': exp
    }, app.config.SECRET_KEY, algorithm='HS256')
    
@pytest_asyncio.fixture
async def get_jwt_access(user_normal, app):
    return get_jwt_for_user(user_normal, app)


@pytest_asyncio.fixture
async def get_jwt_admin_access(user_admin, app):
    return get_jwt_for_user(user_admin, app)


@pytest_asyncio.fixture
async def get_jwt_access_expired(user_admin, app):
    return get_jwt_for_user(user_admin, app, expired=True)

@pytest_asyncio.fixture
async def get_bills_with_ts(async_db_session):
    transacations = TransactionFactory.create_batch(10, session=async_db_session)
    await async_db_session.commit()
    return [t.bill for t in transacations]

@pytest_asyncio.fixture
async def get_user_normal_bill(async_db_session, user_normal):
    transacations = TransactionFactory.create_batch(
        3, 
        session=async_db_session, 
        bill__user=user_normal,
        )
    await async_db_session.commit()
    return [t.bill for t in transacations]

