"""Validações compartilhadas entre criação e atualização."""
from datetime import datetime

from config.constants import (
    COLOR_PATTERN,
    DUE_DATE_FORMAT,
    EMAIL_PATTERN,
    MIN_PASSWORD_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TAGS_SEPARATOR,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALID_ROLES,
    VALID_STATUSES,
)
from middlewares.errors import ValidationError


def require_body(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    return data


def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_required_text(value, message):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(message)
    return value


def validate_title(title):
    validate_required_text(title, "Título é obrigatório")
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError("Título muito longo")
    return title


def validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError("Status inválido")
    return status


def validate_priority(priority):
    if not is_integer(priority):
        raise ValidationError("Prioridade inválida")
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError(f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}")
    return priority


def parse_due_date(value):
    """None/'' limpa a data; string no formato YYYY-MM-DD vira datetime."""
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError("Formato de data inválido. Use YYYY-MM-DD")
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError("Formato de data inválido. Use YYYY-MM-DD") from None


def normalize_tags(tags):
    if tags is None or tags == "":
        return None
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return TAGS_SEPARATOR.join(tags) or None
    if isinstance(tags, str):
        return tags
    raise ValidationError("Tags inválidas")


def parse_optional_int(value, message):
    """Converte parâmetro de query string; vazio vira None."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(message) from None


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError("Email inválido")
    return email


def validate_password(password, message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError("Role inválido")
    return role


def validate_active(active):
    if not isinstance(active, bool):
        raise ValidationError("Active deve ser true ou false")
    return active


def validate_color(color):
    if not isinstance(color, str) or not COLOR_PATTERN.match(color):
        raise ValidationError("Cor inválida. Use o formato #RRGGBB")
    return color
