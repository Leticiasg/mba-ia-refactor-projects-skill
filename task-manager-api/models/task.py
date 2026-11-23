from sqlalchemy import func
from sqlalchemy.orm import joinedload

from config.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS, STATUS_DONE
from models.database import db, utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_detail_dict(self, now=None):
        data = self.to_dict()
        data['overdue'] = self.is_overdue(now)
        return data

    def to_list_item_dict(self, now=None):
        data = self.to_detail_dict(now)
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_user_task_dict(self, now=None):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(now),
        }


def _overdue_condition(now):
    return db.and_(Task.due_date.isnot(None), Task.due_date < now, Task.status.notin_(CLOSED_STATUSES))


def _scoped(query, user_id):
    return query.filter(Task.user_id == user_id) if user_id is not None else query


def get_by_id(task_id):
    return db.session.get(Task, task_id)


def list_with_relations():
    return (Task.query
            .options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
            .all())


def list_by_user(user_id):
    return Task.query.filter_by(user_id=user_id).order_by(Task.id).all()


def search(text=None, status=None, priority=None, user_id=None):
    query = Task.query
    if text:
        pattern = f'%{text}%'
        query = query.filter(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
    if status:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    return query.order_by(Task.id).all()


def count_all(user_id=None):
    return _scoped(Task.query, user_id).count()


def count_by_status(user_id=None):
    query = _scoped(db.session.query(Task.status, func.count(Task.id)), user_id)
    return dict(query.group_by(Task.status).all())


def count_by_priority():
    return dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())


def count_high_priority(max_priority, user_id=None):
    return _scoped(Task.query.filter(Task.priority <= max_priority), user_id).count()


def count_overdue(now, user_id=None):
    return _scoped(Task.query.filter(_overdue_condition(now)), user_id).count()


def list_overdue(now):
    return Task.query.filter(_overdue_condition(now)).order_by(Task.id).all()


def count_created_since(since):
    return Task.query.filter(Task.created_at >= since).count()


def count_done_updated_since(since):
    return Task.query.filter(Task.status == STATUS_DONE, Task.updated_at >= since).count()
