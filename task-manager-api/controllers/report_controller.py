from datetime import timedelta

from config.constants import (
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from controllers.metrics import percentage
from middlewares.errors import NotFoundError
from models.category import Category
from models.database import utcnow
from models.task import Task
from models.user import User


def _status_breakdown(by_status):
    return {
        STATUS_PENDING: by_status.get(STATUS_PENDING, 0),
        STATUS_IN_PROGRESS: by_status.get(STATUS_IN_PROGRESS, 0),
        STATUS_DONE: by_status.get(STATUS_DONE, 0),
        STATUS_CANCELLED: by_status.get(STATUS_CANCELLED, 0),
    }


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    by_priority = Task.count_by_priority()

    overdue_tasks = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in Task.list_overdue(now)
    ]

    user_productivity = [
        {
            'user_id': user_id,
            'user_name': user_name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': percentage(completed, total),
        }
        for user_id, user_name, total, completed in User.productivity()
    ]

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': _status_breakdown(Task.count_by_status()),
        'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': overdue_tasks,
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_done_since(since),
        },
        'user_productivity': user_productivity,
    }


def user_report(user_id):
    user = User.get(user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')

    breakdown = _status_breakdown(Task.count_by_status(user_id=user_id))
    total = sum(breakdown.values())
    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': breakdown[STATUS_DONE],
            'pending': breakdown[STATUS_PENDING],
            'in_progress': breakdown[STATUS_IN_PROGRESS],
            'cancelled': breakdown[STATUS_CANCELLED],
            'overdue': Task.count_overdue(utcnow(), user_id=user_id),
            'high_priority': Task.count_high_priority(user_id),
            'completion_rate': percentage(breakdown[STATUS_DONE], total),
        },
    }
