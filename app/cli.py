# import click
# from sanic import Sanic
# from app.middlewares import _sessionmaker
# from app.models import User, Bill, Transactions

# app = Sanic.get_app()

# @app.command(name='create_user')
# async def create_user(name, email, password, is_admin):
#     session = _sessionmaker()
#     user = User(name=name, email=email, password=password, is_admin=is_admin)
#     user.set_hash_password(password)
#     session.add(user)
#     await session.commit()
#     print(f'User has been created. email: {email} name: {name} password: {password}')
    