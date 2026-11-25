from sqlalchemy import and_, func, or_
from sqlalchemy.orm import joinedload

from config.constants import (
    CLOSED_STATUSES,
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    HIGH_PRIORITY_MAX,
    STATUS_DONE,
)
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

    # ---- serialização ----

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

    def to_dict_with_overdue(self, now=None):
        data = self.to_dict()
        data['overdue'] = self.is_overdue(now)
        return data

    def to_list_item(self, now=None):
        data = self.to_dict_with_overdue(now)
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self, now=None):
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

    # ---- regras da entidade ----

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    @staticmethod
    def overdue_condition(now):
        return and_(
            Task.due_date.isnot(None),
            Task.due_date < now,
            Task.status.notin_(CLOSED_STATUSES),
        )

    # ---- consultas ----

    @staticmethod
    def get(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def list_with_relations():
        return (
            Task.query.options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
            .all()
        )

    @staticmethod
    def list_by_user(user_id):
        return Task.query.filter_by(user_id=user_id).order_by(Task.id).all()

    @staticmethod
    def search(text=None, status=None, priority=None, user_id=None):
        query = Task.query
        if text:
            pattern = f'%{text}%'
            query = query.filter(or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        return query.order_by(Task.id).all()

    @staticmethod
    def count_all():
        return Task.query.count()

    @staticmethod
    def count_by_status(user_id=None):
        query = db.session.query(Task.status, func.count(Task.id))
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        return dict(query.group_by(Task.status).all())

    @staticmethod
    def count_by_priority():
        return dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())

    @staticmethod
    def count_overdue(now, user_id=None):
        query = Task.query.filter(Task.overdue_condition(now))
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        return query.count()

    @staticmethod
    def list_overdue(now):
        return Task.query.filter(Task.overdue_condition(now)).order_by(Task.id).all()

    @staticmethod
    def count_high_priority(user_id):
        return Task.query.filter(Task.user_id == user_id, Task.priority <= HIGH_PRIORITY_MAX).count()

    @staticmethod
    def count_created_since(since):
        return Task.query.filter(Task.created_at >= since).count()

    @staticmethod
    def count_done_since(since):
        return Task.query.filter(Task.status == STATUS_DONE, Task.updated_at >= since).count()

    @staticmethod
    def delete_by_user(user_id):
        Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)

    @staticmethod
    def clear_category(category_id):
        Task.query.filter_by(category_id=category_id).update({'category_id': None}, synchronize_session=False)
