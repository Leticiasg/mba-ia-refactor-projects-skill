import logging

from config.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH
from controllers import validators
from controllers.permissions import ensure_admin, ensure_owner_or_admin
from middlewares.auth import issue_token
from middlewares.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
EMAIL_TAKEN = 'Email já cadastrado'
INVALID_CREDENTIALS = 'Credenciais inválidas'


def _get_user_or_404(user_id):
    user = User.get(user_id)
    if user is None:
        raise NotFoundError(USER_NOT_FOUND)
    return user


def _ensure_email_available(email, current_user_id=None):
    existing = User.find_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError(EMAIL_TAKEN)


def list_users():
    result = []
    for user, task_count in User.list_with_task_counts():
        data = user.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result


def get_user(user_id):
    user = _get_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
    return data


def create_user(data, requester):
    validators.require_body(data)
    name = validators.validate_required_text(data.get('name'), 'Nome é obrigatório')
    email = data.get('email')
    if not email:
        raise ValidationError('Email é obrigatório')
    password = data.get('password')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validators.validate_email(email)
    validators.validate_password(password, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    _ensure_email_available(email)
    role = validators.validate_role(data.get('role', DEFAULT_ROLE))
    if role != DEFAULT_ROLE:
        ensure_admin(requester)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    user.save()
    logger.info('Usuário criado: %s', user.id)
    return user.to_dict()


def update_user(user_id, data, requester):
    user = _get_user_or_404(user_id)
    ensure_owner_or_admin(requester, user.id)
    validators.require_body(data)
    if 'role' in data or 'active' in data:
        ensure_admin(requester)

    if 'name' in data:
        user.name = validators.validate_required_text(data['name'], 'Nome é obrigatório')
    if 'email' in data:
        validators.validate_email(data['email'])
        _ensure_email_available(data['email'], current_user_id=user.id)
        user.email = data['email']
    if 'password' in data:
        user.set_password(validators.validate_password(data['password'], 'Senha muito curta'))
    if 'role' in data:
        user.role = validators.validate_role(data['role'])
    if 'active' in data:
        user.active = validators.validate_active(data['active'])

    user.save()
    logger.info('Usuário atualizado: %s', user.id)
    return user.to_dict()


def delete_user(user_id, requester):
    user = _get_user_or_404(user_id)
    ensure_owner_or_admin(requester, user.id)
    user.delete_with_tasks()
    logger.info('Usuário deletado: %s', user_id)


def get_user_tasks(user_id):
    _get_user_or_404(user_id)
    return [task.to_summary_dict() for task in Task.list_by_user(user_id)]


def login(data):
    validators.require_body(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(email)
    if user is None or not user.check_password(password):
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    if user.has_legacy_password_hash():
        user.set_password(password)
        user.save()
        logger.info('Hash de senha do usuário %s migrado para o formato novo', user.id)

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user),
    }
