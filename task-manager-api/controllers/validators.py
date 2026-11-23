"""Validações reutilizadas pelos controllers."""
from middlewares.errors import ValidationError

INVALID_PAYLOAD_MESSAGE = 'Dados inválidos'


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_payload(data, allow_empty=False):
    """Garante um objeto JSON no corpo. Sem allow_empty, {} também é recusado."""
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError(INVALID_PAYLOAD_MESSAGE)
    return data


def to_id(value):
    """Converte um id vindo do JSON (int ou texto numérico) para int; None se não for id."""
    if is_int(value):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def parse_int_param(raw_value, message):
    """Converte um parâmetro de query string; texto vazio vira None."""
    if raw_value in (None, ''):
        return None
    try:
        return int(raw_value)
    except ValueError:
        raise ValidationError(message) from None
