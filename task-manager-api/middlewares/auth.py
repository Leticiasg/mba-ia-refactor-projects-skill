"""Token assinado de login e identificação de quem chama (Authorization: Bearer <token>)."""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from middlewares.errors import UnauthorizedError
from models.user import User

TOKEN_SALT = 'auth-token'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def create_token(user):
    return _serializer().dumps({'user_id': user.id})


def _user_from_request():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    token = header[len('Bearer '):].strip()
    try:
        payload = _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except (BadSignature, SignatureExpired):
        return None
    user = User.get(payload.get('user_id'))
    if user is None or not user.active:
        return None
    return user


def optional_auth(view):
    """Preenche g.current_user quando há token válido; não bloqueia sem token."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = _user_from_request()
        return view(*args, **kwargs)
    return wrapper


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = _user_from_request()
        if user is None:
            raise UnauthorizedError('Não autorizado')
        g.current_user = user
        return view(*args, **kwargs)
    return wrapper
