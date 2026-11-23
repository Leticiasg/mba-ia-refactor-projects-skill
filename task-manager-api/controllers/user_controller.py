import logging
import re

from config.constants import DEFAULT_ROLE, EMAIL_PATTERN, PASSWORD_MIN_LENGTH, ROLE_ADMIN, VALID_ROLES
from controllers.validators import require_payload
from middlewares.auth import ensure_admin
from middlewares.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models import task as task_model
from models import user as user_model
from models.database import delete, save
from models.user import User

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
INVALID_CREDENTIALS = 'Credenciais inválidas'


def _validate_email(email):
    if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email):
        raise ValidationError('Email inválido')
    return email


def _ensure_email_available(email, current_user_id=None):
    existing = user_model.get_by_email(email)
    if existing is not None and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def _validate_password(password, message):
    if not isinstance(password, str) or len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(message)
    return password


def _validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def list_users():
    return user_model.list_with_task_stats()


def get_user(user_id):
    user = user_model.get_by_id(user_id)
    if user is None:
        raise NotFoundError(USER_NOT_FOUND)
    return user


def get_user_with_tasks(user_id):
    user = get_user(user_id)
    return user, task_model.list_by_user(user_id)


def create_user(data, requester):
    """Cadastro aberto; criar um usuário admin exige que quem chama seja admin."""
    require_payload(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    _validate_email(email)
    _validate_password(password, f'Senha deve ter no mínimo {PASSWORD_MIN_LENGTH} caracteres')
    _ensure_email_available(email)
    _validate_role(role)
    if role == ROLE_ADMIN:
        ensure_admin(requester)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    save(user)
    logger.info('Usuário criado: %s', user.id)
    return user


def update_user(user_id, data, requester):
    """Alterar role ou active exige que quem chama seja admin."""
    user = get_user(user_id)
    require_payload(data)
    if 'role' in data or 'active' in data:
        ensure_admin(requester)

    if 'name' in data and (not isinstance(data['name'], str) or not data['name']):
        raise ValidationError('Nome é obrigatório')
    if 'email' in data:
        _validate_email(data['email'])
        _ensure_email_available(data['email'], current_user_id=user_id)
    if 'password' in data:
        _validate_password(data['password'], 'Senha muito curta')
    if 'role' in data:
        _validate_role(data['role'])
    if 'active' in data and not isinstance(data['active'], bool):
        raise ValidationError('Active deve ser true ou false')

    for field in ('name', 'email', 'role', 'active'):
        if field in data:
            setattr(user, field, data[field])
    if 'password' in data:
        user.set_password(data['password'])
    save(user)
    logger.info('Usuário atualizado: %s', user.id)
    return user


def delete_user(user_id):
    """Apaga o usuário e as tasks dele numa única transação."""
    user = get_user(user_id)
    delete(*task_model.list_by_user(user_id), user)
    logger.info('Usuário deletado: %s', user_id)


def authenticate(data):
    require_payload(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = user_model.get_by_email(email) if isinstance(email, str) else None
    if user is None or not isinstance(password, str) or not user.check_password(password):
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    return user
