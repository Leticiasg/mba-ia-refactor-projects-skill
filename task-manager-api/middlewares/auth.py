"""Token de acesso emitido no login e checagem de administrador."""
from functools import wraps

from flask import current_app, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from middlewares.errors import ForbiddenError, UnauthorizedError
from models import user as user_model

_TOKEN_SALT = 'auth-token'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_TOKEN_SALT)


def generate_token(user):
    return _serializer().dumps({'user_id': user.id})


def get_authenticated_user():
    """Usuário ativo dono do token em 'Authorization: Bearer <token>', ou None."""
    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        return None
    try:
        payload = _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except BadSignature:  # inclui token expirado (SignatureExpired)
        return None
    user = user_model.get_by_id(payload.get('user_id'))
    if user is None or not user.active:
        return None
    return user


def ensure_admin(user):
    if user is None:
        raise UnauthorizedError('Não autorizado')
    if not user.is_admin():
        raise ForbiddenError('Acesso restrito a administradores')


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        ensure_admin(get_authenticated_user())
        return view(*args, **kwargs)
    return wrapper
