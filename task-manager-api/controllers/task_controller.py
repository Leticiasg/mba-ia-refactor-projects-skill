import logging

from config.constants import DEFAULT_PRIORITY, DEFAULT_STATUS, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING
from controllers import permissions, validators
from controllers.metrics import percentage
from middlewares.errors import ForbiddenError, NotFoundError
from models.category import Category
from models.database import db, utcnow
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


def _get_task_or_404(task_id):
    task = Task.get(task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_user_exists(user_id):
    if user_id and User.get(user_id) is None:
        raise NotFoundError('Usuário não encontrado')


def _ensure_category_exists(category_id):
    if category_id and Category.get(category_id) is None:
        raise NotFoundError('Categoria não encontrada')


def _ensure_can_assign(requester, user_id):
    """Usuário comum só cria/atribui tasks para si; admin atribui para qualquer um."""
    if not requester.is_admin() and user_id != requester.id:
        raise ForbiddenError('Sem permissão para atribuir task a outro usuário')


def list_tasks():
    now = utcnow()
    return [task.to_list_item(now) for task in Task.list_with_relations()]


def get_task(task_id):
    return _get_task_or_404(task_id).to_dict_with_overdue()


def search_tasks(text, status, priority, user_id):
    tasks = Task.search(
        text=text,
        status=status,
        priority=validators.parse_optional_int(priority, 'Prioridade'),
        user_id=validators.parse_optional_int(user_id, 'user_id'),
    )
    return [task.to_dict() for task in tasks]


def get_stats():
    now = utcnow()
    total = Task.count_all()
    by_status = Task.count_by_status()
    done = by_status.get(STATUS_DONE, 0)
    return {
        'total': total,
        'pending': by_status.get(STATUS_PENDING, 0),
        'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
        'done': done,
        'cancelled': by_status.get(STATUS_CANCELLED, 0),
        'overdue': Task.count_overdue(now),
        'completion_rate': percentage(done, total),
    }


def create_task(data, requester, notifier=None):
    data = validators.require_body(data)
    title = validators.validate_title(data.get('title'))
    status = validators.validate_status(data.get('status', DEFAULT_STATUS))
    priority = validators.validate_priority(data.get('priority', DEFAULT_PRIORITY))

    user_id = data.get('user_id', None if requester.is_admin() else requester.id)
    _ensure_can_assign(requester, user_id)
    _ensure_user_exists(user_id)
    category_id = data.get('category_id')
    _ensure_category_exists(category_id)

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
        due_date=validators.parse_due_date(data.get('due_date')),
        tags=validators.normalize_tags(data.get('tags')) or None,
    )
    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: %s", task.id)

    if notifier is not None and task.user is not None:
        notifier.notify_task_assigned(task.user, task)
    return task.to_dict()


def update_task(task_id, data, requester):
    task = _get_task_or_404(task_id)
    permissions.ensure_owner_or_admin(requester, task.user_id)
    data = validators.require_body(data)

    if 'title' in data:
        task.title = validators.validate_title(data['title'])
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = validators.validate_status(data['status'])
    if 'priority' in data:
        task.priority = validators.validate_priority(data['priority'])
    if 'user_id' in data:
        _ensure_can_assign(requester, data['user_id'])
        _ensure_user_exists(data['user_id'])
        task.user_id = data['user_id']
    if 'category_id' in data:
        _ensure_category_exists(data['category_id'])
        task.category_id = data['category_id']
    if 'due_date' in data:
        task.due_date = validators.parse_due_date(data['due_date'])
    if 'tags' in data:
        task.tags = validators.normalize_tags(data['tags'])

    task.updated_at = utcnow()
    db.session.commit()
    logger.info("Task atualizada: %s", task.id)
    return task.to_dict()


def delete_task(task_id, requester):
    task = _get_task_or_404(task_id)
    permissions.ensure_owner_or_admin(requester, task.user_id)
    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: %s", task_id)
