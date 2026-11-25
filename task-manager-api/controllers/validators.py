"""Validação de entrada compartilhada entre criação e atualização."""
import re
from datetime import datetime

from config.constants import (
    COLOR_PATTERN,
    DATE_FORMAT,
    EMAIL_PATTERN,
    MIN_PASSWORD_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALID_ROLES,
    VALID_STATUSES,
)
from middlewares.errors import ValidationError


def require_body(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def validate_title(title):
    if not isinstance(title, str) or not title:
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
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError('Prioridade inválida')
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return priority


def parse_due_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')


def normalize_tags(tags):
    if isinstance(tags, list):
        return ','.join(str(tag) for tag in tags)
    return tags


def parse_optional_int(value, field_label):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f'{field_label} inválido')


def validate_email(email):
    if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password, message='Senha deve ter no mínimo 4 caracteres'):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('Nome é obrigatório')
    return name


def validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_active(active):
    if not isinstance(active, bool):
        raise ValidationError('Active inválido')
    return active


def validate_color(color):
    if not isinstance(color, str) or not re.match(COLOR_PATTERN, color):
        raise ValidationError('Cor inválida')
    return color
