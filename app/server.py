from functools import partial
from sanic import Sanic, text
from sanic_ext import Extend

from app.config import DevConfig
from sanic.worker.loader import AppLoader

def create_app(app_name: str = 'Default') -> Sanic:
    
    app = Sanic(app_name)
    Extend(app)

    # Config
    # db_settings = {
    #     'POSTGRES_HOST':  os.getenv('POSTGRES_HOST'),
    #     'POSTGRES_DB': os.getenv('POSTGRES_DB'),
    #     'POSTGRES_USER': os.getenv('POSTGRES_USER'),
    #     'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
    #     'SECRET_KEY': os.getenv('SECRET_KEY'),
    #     'SECRET_KEY': os.getenv('SECRET_KEY'),
    #     'ALGO': os.getenv('ALGORITHM'),
    #     'LOG_LEVEL': os.getenv('LOG_LEVEL', default='DEBUG'),
    # }
    app.config.update_config(DevConfig)

    from app.views import api_blueprint

    app.blueprint(api_blueprint)

    from app.middlewares import setup_middleware
    setup_middleware(app)

    # Health check
    @app.get('/ping')
    async def ping(request):
        return text("OK!")

    return app
    
if __name__ == '__main__':
    loader = AppLoader(factory=partial(create_app, 'MyApp'))
    app = loader.load()
    app.prepare(host='0.0.0.0', port=8000)
    Sanic.serve(primary=app, app_loader=loader)
    # app.run(host='0.0.0.0', port=8000)
