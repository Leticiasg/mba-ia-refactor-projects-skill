from datetime import timedelta

from config.constants import (
    HIGH_PRIORITY_MAX,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_DONE,
    VALID_STATUSES,
)
from controllers.task_controller import completion_rate
from middlewares.errors import NotFoundError
from models.category import Category
from models.database import utcnow
from models.task import Task
from models.user import User


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    status_counts = Task.count_by_status()
    priority_counts = Task.count_by_priority()
    totals_by_user = Task.totals_by_user()

    overdue_tasks = [
        {
            "id": task.id,
            "title": task.title,
            "due_date": str(task.due_date),
            "days_overdue": (now - task.due_date).days,
        }
        for task in Task.list_overdue(now)
    ]

    user_productivity = []
    for user in User.list_all():
        total, completed = totals_by_user.get(user.id, (0, 0))
        user_productivity.append({
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": completion_rate(completed, total),
        })

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": Task.count_all(),
            "total_users": User.count_all(),
            "total_categories": Category.count_all(),
        },
        "tasks_by_status": {status: status_counts.get(status, 0) for status in VALID_STATUSES},
        "tasks_by_priority": {
            label: priority_counts.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
        },
        "overdue": {"count": len(overdue_tasks), "tasks": overdue_tasks},
        "recent_activity": {
            "tasks_created_last_7_days": Task.count_created_since(since),
            "tasks_completed_last_7_days": Task.count_completed_since(since),
        },
        "user_productivity": user_productivity,
    }


def user_report(user_id):
    user = User.get_by_id(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")

    status_counts = Task.count_by_status(user_id=user_id)
    total = sum(status_counts.values())
    done = status_counts.get(STATUS_DONE, 0)
    statistics = {status: status_counts.get(status, 0) for status in VALID_STATUSES}
    statistics.update({
        "total_tasks": total,
        "overdue": Task.count_overdue(utcnow(), user_id=user_id),
        "high_priority": Task.count_high_priority(user_id, HIGH_PRIORITY_MAX),
        "completion_rate": completion_rate(done, total),
    })
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": statistics,
    }
