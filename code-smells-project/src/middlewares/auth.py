import hmac
from functools import wraps

from flask import current_app, jsonify, request


def require_admin(view):
    """Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem token configurado, a rota fica bloqueada."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN", "")
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(recebido, esperado):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)

    return wrapper
