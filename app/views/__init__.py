from sanic import Blueprint

# from .login import register_login_view
from .users import api_user_bp
from .auth import api_auth_bp
from .payment import wh_pay_bp

api_blueprint = Blueprint.group(
    api_user_bp, 
    api_auth_bp, 
    wh_pay_bp,
    url_prefix="/api",
    )
