"""Validações de entrada compartilhadas por criação e atualização."""
import re
from datetime import datetime

from config.constants import (COLOR_PATTERN, DUE_DATE_FORMAT, EMAIL_PATTERN, MIN_PASSWORD_LENGTH,
                              PRIORITY_MAX, PRIORITY_MIN, TAGS_SEPARATOR, TITLE_MAX_LENGTH,
                              TITLE_MIN_LENGTH, VALID_ROLES, VALID_STATUSES)
from middlewares.errors import ValidationError

INVALID_DATA_MESSAGE = 'Dados inválidos'


def require_body(data):
    if not data or not isinstance(data, dict):
        raise ValidationError(INVALID_DATA_MESSAGE)
    return data


def validate_title(title):
    if not title or not isinstance(title, str):
        raise ValidationError('Título é obrigatório')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    is_int = isinstance(priority, int) and not isinstance(priority, bool)
    if not is_int or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return priority


def parse_due_date(value, error_message):
    if not isinstance(value, str):
        raise ValidationError(error_message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(error_message) from None


def normalize_tags(tags):
    if tags is None or isinstance(tags, str):
        return tags
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return TAGS_SEPARATOR.join(tags)
    raise ValidationError('Tags inválidas')


def validate_required_text(value, message):
    if not value or not isinstance(value, str) or not value.strip():
        raise ValidationError(message)
    return value


def validate_email(email):
    if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password, message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_active(active):
    if not isinstance(active, bool):
        raise ValidationError('Active deve ser true ou false')
    return active


def validate_color(color):
    if not isinstance(color, str) or not re.match(COLOR_PATTERN, color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


def parse_int_param(value, name):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido') from None
