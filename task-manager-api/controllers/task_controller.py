import logging
from datetime import datetime

from flask import current_app

from config.constants import (
    DATE_FORMAT, DEFAULT_PRIORITY, DEFAULT_STATUS, PRIORITY_MAX, PRIORITY_MIN,
    STATUS_DONE, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH, VALID_STATUSES,
)
from controllers.validators import is_int, parse_int_param, require_payload, to_id
from middlewares.errors import NotFoundError, ValidationError
from models import category as category_model
from models import task as task_model
from models import user as user_model
from models.database import delete, save, utcnow
from models.task import Task
from utils.helpers import calculate_percentage

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'


# ---- validação (a mesma na criação e na atualização) ----

def _validate_title(title):
    if not isinstance(title, str) or not title:
        raise ValidationError('Título é obrigatório')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _validate_priority(priority):
    if not is_int(priority) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return priority


def _resolve_user_id(raw_user_id):
    if not raw_user_id:
        return None
    user_id = to_id(raw_user_id)
    if user_id is None or user_model.get_by_id(user_id) is None:
        raise NotFoundError(USER_NOT_FOUND)
    return user_id


def _resolve_category_id(raw_category_id):
    if not raw_category_id:
        return None
    category_id = to_id(raw_category_id)
    if category_id is None or category_model.get_by_id(category_id) is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)
    return category_id


def _parse_due_date(raw_date):
    if not raw_date:
        return None
    if not isinstance(raw_date, str):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
    try:
        return datetime.strptime(raw_date, DATE_FORMAT)
    except ValueError:
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD') from None


def _normalize_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return ','.join(tags)
    if tags is None or isinstance(tags, str):
        return tags
    raise ValidationError('Tags inválidas')


def _notify_assignment(task):
    if task.user_id is None:
        return
    assignee = user_model.get_by_id(task.user_id)
    if assignee is not None:
        current_app.extensions['notification_service'].notify_task_assigned(assignee, task)


# ---- casos de uso ----

def list_tasks():
    return task_model.list_with_relations()


def get_task(task_id):
    task = task_model.get_by_id(task_id)
    if task is None:
        raise NotFoundError(TASK_NOT_FOUND)
    return task


def create_task(data):
    require_payload(data)
    title = _validate_title(data.get('title'))
    status = _validate_status(data.get('status', DEFAULT_STATUS))
    priority = _validate_priority(data.get('priority', DEFAULT_PRIORITY))
    user_id = _resolve_user_id(data.get('user_id'))
    category_id = _resolve_category_id(data.get('category_id'))
    due_date = _parse_due_date(data.get('due_date'))
    tags = data.get('tags')

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
        due_date=due_date,
        tags=_normalize_tags(tags) if tags else None,
    )
    save(task)
    logger.info('Task criada: %s', task.id)
    _notify_assignment(task)
    return task


def update_task(task_id, data):
    task = get_task(task_id)
    require_payload(data)

    changes = {}
    if 'title' in data:
        changes['title'] = _validate_title(data['title'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'status' in data:
        changes['status'] = _validate_status(data['status'])
    if 'priority' in data:
        changes['priority'] = _validate_priority(data['priority'])
    if 'user_id' in data:
        changes['user_id'] = _resolve_user_id(data['user_id'])
    if 'category_id' in data:
        changes['category_id'] = _resolve_category_id(data['category_id'])
    if 'due_date' in data:
        changes['due_date'] = _parse_due_date(data['due_date'])
    if 'tags' in data:
        changes['tags'] = _normalize_tags(data['tags'])

    previous_user_id = task.user_id
    for field, value in changes.items():
        setattr(task, field, value)
    task.updated_at = utcnow()
    save(task)
    logger.info('Task atualizada: %s', task.id)
    if task.user_id != previous_user_id:
        _notify_assignment(task)
    return task


def delete_task(task_id):
    task = get_task(task_id)
    delete(task)
    logger.info('Task deletada: %s', task_id)


def search_tasks(text, status, raw_priority, raw_user_id):
    priority = parse_int_param(raw_priority, 'Prioridade inválida')
    user_id = parse_int_param(raw_user_id, 'user_id inválido')
    return task_model.search(text=text, status=status, priority=priority, user_id=user_id)


def task_stats():
    total = task_model.count_all()
    by_status = task_model.count_by_status()
    done = by_status.get(STATUS_DONE, 0)
    stats = {status: by_status.get(status, 0) for status in VALID_STATUSES}
    stats.update({
        'total': total,
        'overdue': task_model.count_overdue(utcnow()),
        'completion_rate': calculate_percentage(done, total),
    })
    return stats
