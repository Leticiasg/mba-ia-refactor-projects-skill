import hmac
from functools import wraps

from flask import current_app, request

from src.middlewares.errors import UnauthorizedError


def require_admin(view):
    """Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem token configurado, bloqueia."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN") or ""
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(recebido, esperado):
            raise UnauthorizedError("Não autorizado")
        return view(*args, **kwargs)

    return wrapper
