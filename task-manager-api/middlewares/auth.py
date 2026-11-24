"""Token de login assinado e checagem de autenticação.

O cliente envia o token devolvido por POST /login no header
`Authorization: Bearer <token>`.
"""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from middlewares.errors import UnauthorizedError
from models.user import User

TOKEN_SALT = 'auth-token'
BEARER_PREFIX = 'Bearer '
UNAUTHORIZED_MESSAGE = 'Não autorizado'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def issue_token(user):
    return _serializer().dumps({'user_id': user.id})


def _user_from_request():
    header = request.headers.get('Authorization', '')
    if not header.startswith(BEARER_PREFIX):
        return None
    try:
        payload = _serializer().loads(header[len(BEARER_PREFIX):],
                                      max_age=current_app.config['AUTH_TOKEN_MAX_AGE_SECONDS'])
    except BadSignature:
        return None
    user = User.get(payload.get('user_id'))
    if user is None or not user.active:
        return None
    return user


def current_user():
    """Usuário autenticado na requisição, ou None (rotas onde o token é opcional)."""
    if 'current_user' not in g:
        g.current_user = _user_from_request()
    return g.current_user


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            raise UnauthorizedError(UNAUTHORIZED_MESSAGE)
        return view(*args, **kwargs)
    return wrapper
