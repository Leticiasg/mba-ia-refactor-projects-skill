from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from config.constants import (CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS,
                              STATUS_DONE, TAGS_SEPARATOR)
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

    # ---- regras da entidade -------------------------------------------------

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    def tag_list(self):
        return self.tags.split(TAGS_SEPARATOR) if self.tags else []

    # ---- serialização -------------------------------------------------------

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
            'tags': self.tag_list(),
        }

    def to_dict_with_overdue(self):
        data = self.to_dict()
        data['overdue'] = self.is_overdue()
        return data

    def to_list_item(self):
        data = self.to_dict_with_overdue()
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # ---- consultas ----------------------------------------------------------

    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        return (cls.query
                .options(joinedload(cls.user), joinedload(cls.category))
                .order_by(cls.id)
                .all())

    @classmethod
    def list_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).order_by(cls.id).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = cls.query
        if text:
            pattern = f'%{text}%'
            query = query.filter(or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.filter(cls.status == status)
        if priority is not None:
            query = query.filter(cls.priority == priority)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.order_by(cls.id).all()

    @classmethod
    def _overdue_filter(cls, now):
        return [cls.due_date.isnot(None), cls.due_date < now, cls.status.notin_(CLOSED_STATUSES)]

    @classmethod
    def count_all(cls, user_id=None):
        query = db.session.query(func.count(cls.id))
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.scalar()

    @classmethod
    def count_by_status(cls, user_id=None):
        query = db.session.query(cls.status, func.count(cls.id))
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return dict(query.group_by(cls.status).all())

    @classmethod
    def count_by_priority(cls):
        return dict(db.session.query(cls.priority, func.count(cls.id)).group_by(cls.priority).all())

    @classmethod
    def count_overdue(cls, now, user_id=None):
        query = db.session.query(func.count(cls.id)).filter(*cls._overdue_filter(now))
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.scalar()

    @classmethod
    def list_overdue(cls, now):
        return cls.query.filter(*cls._overdue_filter(now)).order_by(cls.id).all()

    @classmethod
    def count_high_priority(cls, user_id, high_priority_max):
        return (db.session.query(func.count(cls.id))
                .filter(cls.user_id == user_id, cls.priority <= high_priority_max)
                .scalar())

    @classmethod
    def count_created_since(cls, since):
        return db.session.query(func.count(cls.id)).filter(cls.created_at >= since).scalar()

    @classmethod
    def count_done_since(cls, since):
        return (db.session.query(func.count(cls.id))
                .filter(cls.status == STATUS_DONE, cls.updated_at >= since)
                .scalar())

    @staticmethod
    def since_days(days, now=None):
        return (now or utcnow()) - timedelta(days=days)

    # ---- gravação -----------------------------------------------------------

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
