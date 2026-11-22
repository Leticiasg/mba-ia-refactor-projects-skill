"""Token assinado (itsdangerous, já instalado com o Flask) enviado como `Authorization: Bearer <token>`."""
from flask import current_app, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from models.user import User

_TOKEN_SALT = "auth-token"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_TOKEN_SALT)


def issue_token(user):
    return _serializer().dumps({"user_id": user.id})


def get_current_user():
    """Usuário ativo dono do token da requisição, ou None se não houver token válido."""
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE_SECONDS"])
    except BadSignature:  # inclui token expirado
        return None
    user = User.get_by_id(payload.get("user_id"))
    if user is None or not user.active:
        return None
    return user
