"""Autenticação por token assinado (Authorization: Bearer <token>)."""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from src.middlewares.errors import ForbiddenError, UnauthorizedError
from src.models import usuario_model
from src.models.database import get_db

_TOKEN_SALT = "auth-token"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_TOKEN_SALT)


def gerar_token(usuario_id):
    return _serializer().dumps({"usuario_id": usuario_id})


def _usuario_autenticado():
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE_SECONDS"])
    except BadSignature:  # inclui token expirado
        return None
    return usuario_model.buscar_por_id(get_db(), payload.get("usuario_id"))


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        usuario = _usuario_autenticado()
        if usuario is None:
            raise UnauthorizedError("Não autorizado")
        g.usuario = usuario
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        usuario = _usuario_autenticado()
        if usuario is None:
            raise UnauthorizedError("Não autorizado")
        if not usuario_model.is_admin(usuario):
            raise ForbiddenError("Acesso restrito a administradores")
        g.usuario = usuario
        return view(*args, **kwargs)
    return wrapper
