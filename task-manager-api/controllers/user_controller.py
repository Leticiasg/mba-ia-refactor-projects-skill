import logging

from config.constants import DEFAULT_ROLE, ROLE_ADMIN
from controllers import validators
from middlewares.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from models.database import db, transaction
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


def _get_user_or_404(user_id):
    user = User.get_by_id(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")
    return user


def _require_admin(actor):
    if actor is None:
        raise UnauthorizedError("Token de administrador obrigatório")
    if not actor.is_admin():
        raise ForbiddenError("Apenas administradores podem executar esta ação")


def _ensure_email_available(email, current_user_id=None):
    existing = User.get_by_email(email)
    if existing is not None and existing.id != current_user_id:
        raise ConflictError("Email já cadastrado")


def list_users():
    totals = Task.totals_by_user()
    result = []
    for user in User.list_all():
        data = user.to_dict()
        data["task_count"] = totals.get(user.id, (0, 0))[0]
        result.append(data)
    return result


def get_user(user_id):
    user = _get_user_or_404(user_id)
    data = user.to_dict()
    data["tasks"] = [task.to_dict() for task in Task.list_by_user(user_id)]
    return data


def list_user_tasks(user_id):
    _get_user_or_404(user_id)
    return [task.to_summary_dict() for task in Task.list_by_user(user_id)]


def create_user(data, actor):
    """Cadastro público; criar um usuário com role admin exige token de admin."""
    validators.require_body(data)
    name = validators.validate_required_text(data.get("name"), "Nome é obrigatório")
    email = data.get("email")
    if not email:
        raise ValidationError("Email é obrigatório")
    password = data.get("password")
    if not password:
        raise ValidationError("Senha é obrigatória")
    role = data.get("role", DEFAULT_ROLE)

    validators.validate_email(email)
    validators.validate_password(password, "Senha deve ter no mínimo 4 caracteres")
    _ensure_email_available(email)
    validators.validate_role(role)
    if role == ROLE_ADMIN:
        _require_admin(actor)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    with transaction("Erro ao criar usuário"):
        db.session.add(user)
    logger.info("Usuário criado: %s", user.id)
    return user.to_dict()


def update_user(user_id, data, actor):
    """Atualização pública, exceto mudar role ou active, que exige token de admin."""
    user = _get_user_or_404(user_id)
    validators.require_body(data)

    changes_privileges = ("role" in data and data["role"] != user.role) or (
        "active" in data and data["active"] != user.active
    )
    if changes_privileges:
        _require_admin(actor)

    changes = {}
    if "name" in data:
        changes["name"] = validators.validate_required_text(data["name"], "Nome é obrigatório")
    if "email" in data:
        changes["email"] = validators.validate_email(data["email"])
        _ensure_email_available(changes["email"], current_user_id=user_id)
    if "password" in data:
        validators.validate_password(data["password"], "Senha muito curta")
    if "role" in data:
        changes["role"] = validators.validate_role(data["role"])
    if "active" in data:
        changes["active"] = validators.validate_active(data["active"])

    with transaction("Erro ao atualizar"):
        for field, value in changes.items():
            setattr(user, field, value)
        if "password" in data:
            user.set_password(data["password"])
    return user.to_dict()


def delete_user(user_id):
    user = _get_user_or_404(user_id)
    with transaction("Erro ao deletar"):
        Task.delete_by_user(user_id)
        db.session.delete(user)
    logger.info("Usuário deletado: %s", user_id)


def authenticate(data):
    validators.require_body(data)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(password, str):
        raise UnauthorizedError("Credenciais inválidas")

    user = User.get_by_email(email)
    if user is None or not user.check_password(password):
        raise UnauthorizedError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")

    if user.has_legacy_password_hash():
        with transaction("Erro ao atualizar senha"):
            user.set_password(password)
        logger.info("Hash de senha migrado para o formato novo: usuário %s", user.id)
    return user
