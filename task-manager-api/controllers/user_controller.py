import logging

from config.constants import DEFAULT_ROLE, ROLE_USER
from controllers import permissions, validators
from middlewares.auth import create_token
from middlewares.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.database import db, utcnow
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


def _get_user_or_404(user_id):
    user = User.get(user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_email_free(email, current_user_id=None):
    existing = User.get_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


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


def get_user_tasks(user_id):
    _get_user_or_404(user_id)
    now = utcnow()
    return [task.to_summary_dict(now) for task in Task.list_by_user(user_id)]


def create_user(data, requester):
    data = validators.require_body(data)
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
    validators.validate_name(name)
    validators.validate_email(email)
    validators.validate_password(password)
    _ensure_email_free(email)
    validators.validate_role(role)
    if role != ROLE_USER:
        # Cadastro é aberto, mas só um admin cria contas com privilégio.
        permissions.ensure_admin(requester)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info("Usuário criado: %s", user.id)
    return user.to_dict()


def update_user(user_id, data, requester):
    user = _get_user_or_404(user_id)
    permissions.ensure_owner_or_admin(requester, user.id)
    data = validators.require_body(data)
    if 'role' in data or 'active' in data:
        permissions.ensure_admin(requester)

    if 'name' in data:
        user.name = validators.validate_name(data['name'])
    if 'email' in data:
        validators.validate_email(data['email'])
        _ensure_email_free(data['email'], current_user_id=user.id)
        user.email = data['email']
    if 'password' in data:
        user.set_password(validators.validate_password(data['password'], 'Senha muito curta'))
    if 'role' in data:
        user.role = validators.validate_role(data['role'])
    if 'active' in data:
        user.active = validators.validate_active(data['active'])

    db.session.commit()
    return user.to_dict()


def delete_user(user_id, requester):
    user = _get_user_or_404(user_id)
    permissions.ensure_owner_or_admin(requester, user.id)
    # Tasks e usuário saem na mesma transação.
    Task.delete_by_user(user_id)
    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: %s", user_id)


def login(data):
    data = validators.require_body(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.get_by_email(email)
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': create_token(user),
    }
