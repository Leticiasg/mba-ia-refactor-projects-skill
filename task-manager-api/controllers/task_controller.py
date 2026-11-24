import logging

from flask import current_app

from config.constants import DEFAULT_PRIORITY, DEFAULT_STATUS, PERCENT_DECIMALS, STATUS_DONE, VALID_STATUSES
from controllers import validators
from controllers.permissions import ensure_owner_or_admin
from middlewares.errors import NotFoundError
from models.category import Category
from models.database import utcnow
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'
CREATE_DATE_ERROR = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_ERROR = 'Formato de data inválido'


def completion_rate(done, total):
    return round((done / total) * 100, PERCENT_DECIMALS) if total > 0 else 0


def _notifier():
    return current_app.extensions['notification_service']


def _get_task_or_404(task_id):
    task = Task.get(task_id)
    if task is None:
        raise NotFoundError(TASK_NOT_FOUND)
    return task


def _get_assignee(user_id):
    if not user_id:
        return None
    user = User.get(user_id)
    if user is None:
        raise NotFoundError(USER_NOT_FOUND)
    return user


def _ensure_category_exists(category_id):
    if category_id and Category.get(category_id) is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)


def list_tasks():
    return [task.to_list_item() for task in Task.list_with_relations()]


def get_task(task_id):
    return _get_task_or_404(task_id).to_dict_with_overdue()


def create_task(data):
    validators.require_body(data)
    title = validators.validate_title(data.get('title'))
    status = validators.validate_status(data.get('status', DEFAULT_STATUS))
    priority = validators.validate_priority(data.get('priority', DEFAULT_PRIORITY))
    assignee = _get_assignee(data.get('user_id'))
    _ensure_category_exists(data.get('category_id'))

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=data.get('user_id'),
        category_id=data.get('category_id'),
    )
    if data.get('due_date'):
        task.due_date = validators.parse_due_date(data['due_date'], CREATE_DATE_ERROR)
    if data.get('tags'):
        task.tags = validators.normalize_tags(data['tags'])

    task.save()
    logger.info('Task criada: %s', task.id)
    if assignee:
        _notifier().notify_task_assigned(assignee, task)
    return task.to_dict()


def update_task(task_id, data):
    task = _get_task_or_404(task_id)
    validators.require_body(data)

    if 'title' in data:
        task.title = validators.validate_title(data['title'])
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = validators.validate_status(data['status'])
    if 'priority' in data:
        task.priority = validators.validate_priority(data['priority'])

    new_assignee = None
    if 'user_id' in data:
        new_assignee = _get_assignee(data['user_id'])
        if new_assignee and task.user_id == new_assignee.id:
            new_assignee = None
        task.user_id = data['user_id']
    if 'category_id' in data:
        _ensure_category_exists(data['category_id'])
        task.category_id = data['category_id']
    if 'due_date' in data:
        due_date = data['due_date']
        task.due_date = validators.parse_due_date(due_date, UPDATE_DATE_ERROR) if due_date else None
    if 'tags' in data:
        task.tags = validators.normalize_tags(data['tags'])

    task.updated_at = utcnow()
    task.save()
    logger.info('Task atualizada: %s', task.id)
    if new_assignee:
        _notifier().notify_task_assigned(new_assignee, task)
    return task.to_dict()


def delete_task(task_id, requester):
    task = _get_task_or_404(task_id)
    ensure_owner_or_admin(requester, task.user_id)
    task.delete()
    logger.info('Task deletada: %s', task_id)


def search_tasks(text, status, priority, user_id):
    tasks = Task.search(
        text=text,
        status=status,
        priority=validators.parse_int_param(priority, 'priority'),
        user_id=validators.parse_int_param(user_id, 'user_id'),
    )
    return [task.to_dict() for task in tasks]


def task_stats():
    counts = Task.count_by_status()
    total = sum(counts.values())
    done = counts.get(STATUS_DONE, 0)
    stats = {status: counts.get(status, 0) for status in VALID_STATUSES}
    stats.update({
        'total': total,
        'overdue': Task.count_overdue(utcnow()),
        'completion_rate': completion_rate(done, total),
    })
    return stats
