from datetime import timedelta

from config.constants import HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_DONE, VALID_STATUSES
from controllers.user_controller import get_user
from models import category as category_model
from models import task as task_model
from models import user as user_model
from models.database import utcnow
from utils.helpers import calculate_percentage


def _status_breakdown(user_id=None):
    counts = task_model.count_by_status(user_id)
    return {status: counts.get(status, 0) for status in VALID_STATUSES}


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    priority_counts = task_model.count_by_priority()
    overdue_tasks = task_model.list_overdue(now)
    users_stats = user_model.list_with_task_stats()

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': task_model.count_all(),
            'total_users': len(users_stats),
            'total_categories': category_model.count_all(),
        },
        'tasks_by_status': _status_breakdown(),
        'tasks_by_priority': {label: priority_counts.get(priority, 0)
                              for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [{
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (now - task.due_date).days,
            } for task in overdue_tasks],
        },
        'recent_activity': {
            'tasks_created_last_7_days': task_model.count_created_since(since),
            'tasks_completed_last_7_days': task_model.count_done_updated_since(since),
        },
        'user_productivity': [{
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': calculate_percentage(done, total),
        } for user, total, done in users_stats],
    }


def user_report(user_id):
    user = get_user(user_id)
    by_status = _status_breakdown(user_id)
    total = task_model.count_all(user_id)
    statistics = dict(by_status)
    statistics.update({
        'total_tasks': total,
        'overdue': task_model.count_overdue(utcnow(), user_id),
        'high_priority': task_model.count_high_priority(HIGH_PRIORITY_MAX, user_id),
        'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
    })
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': statistics,
    }
