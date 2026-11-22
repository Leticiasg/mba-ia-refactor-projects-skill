import logging

from config.constants import DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, STATUS_DONE, VALID_STATUSES
from controllers import validators
from middlewares.errors import NotFoundError
from models.category import Category
from models.database import db, transaction, utcnow
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


def _get_task_or_404(task_id):
    task = Task.get_by_id(task_id)
    if task is None:
        raise NotFoundError("Task não encontrada")
    return task


def _ensure_user_exists(user_id):
    if user_id and User.get_by_id(user_id) is None:
        raise NotFoundError("Usuário não encontrado")


def _ensure_category_exists(category_id):
    if category_id and Category.get_by_id(category_id) is None:
        raise NotFoundError("Categoria não encontrada")


def list_tasks():
    return [task.to_list_dict() for task in Task.list_all_with_relations()]


def get_task(task_id):
    return _get_task_or_404(task_id).to_dict_with_overdue()


def create_task(data):
    validators.require_body(data)
    title = validators.validate_title(data.get("title"))
    status = validators.validate_status(data.get("status", DEFAULT_TASK_STATUS))
    priority = validators.validate_priority(data.get("priority", DEFAULT_PRIORITY))
    user_id = data.get("user_id")
    category_id = data.get("category_id")
    _ensure_user_exists(user_id)
    _ensure_category_exists(category_id)

    task = Task(
        title=title,
        description=data.get("description", ""),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
        due_date=validators.parse_due_date(data.get("due_date")),
        tags=validators.normalize_tags(data.get("tags")),
    )
    with transaction("Erro ao criar task"):
        db.session.add(task)
    logger.info("Task criada: %s", task.id)
    return task.to_dict()


def update_task(task_id, data):
    task = _get_task_or_404(task_id)
    validators.require_body(data)

    changes = {}
    if "title" in data:
        changes["title"] = validators.validate_title(data["title"])
    if "description" in data:
        changes["description"] = data["description"]
    if "status" in data:
        changes["status"] = validators.validate_status(data["status"])
    if "priority" in data:
        changes["priority"] = validators.validate_priority(data["priority"])
    if "user_id" in data:
        _ensure_user_exists(data["user_id"])
        changes["user_id"] = data["user_id"]
    if "category_id" in data:
        _ensure_category_exists(data["category_id"])
        changes["category_id"] = data["category_id"]
    if "due_date" in data:
        changes["due_date"] = validators.parse_due_date(data["due_date"])
    if "tags" in data:
        changes["tags"] = validators.normalize_tags(data["tags"])

    with transaction("Erro ao atualizar"):
        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = utcnow()
    logger.info("Task atualizada: %s", task.id)
    return task.to_dict()


def delete_task(task_id):
    task = _get_task_or_404(task_id)
    with transaction("Erro ao deletar"):
        db.session.delete(task)
    logger.info("Task deletada: %s", task_id)


def search_tasks(text, status, priority, user_id):
    tasks = Task.search(
        text=text,
        status=status,
        priority=validators.parse_optional_int(priority, "Prioridade inválida"),
        user_id=validators.parse_optional_int(user_id, "Usuário inválido"),
    )
    return [task.to_dict() for task in tasks]


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


def task_stats():
    counts = Task.count_by_status()
    total = sum(counts.values())
    stats = {status: counts.get(status, 0) for status in VALID_STATUSES}
    stats["total"] = total
    stats["overdue"] = Task.count_overdue(utcnow())
    stats["completion_rate"] = completion_rate(counts.get(STATUS_DONE, 0), total)
    return stats
