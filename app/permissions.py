from functools import wraps

from sanic import Unauthorized, Forbidden
             
def login_required(f):
    async def decorated_function(request, *args, **kwargs):
        if not request.ctx.user_id:
            raise Unauthorized("Missing or invalid token")
        return await f(request, *args, **kwargs)
    return decorated_function

def is_admin_permission(f):
    @wraps(f)
    async def decorated_function(request, *args, **kwargs):
        if not request.ctx.user_id:
            raise Unauthorized("Missing or invalid token")
        if not request.ctx.is_admin:
            raise Forbidden('Only Admin permission')
        return await f(request, *args, **kwargs)
    
    return decorated_function
