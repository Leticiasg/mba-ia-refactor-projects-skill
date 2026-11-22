from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import joinedload

from config.constants import (
    CLOSED_STATUSES,
    DEFAULT_PRIORITY,
    DEFAULT_TASK_STATUS,
    STATUS_DONE,
    TAGS_SEPARATOR,
    TITLE_MAX_LENGTH,
)
from models.database import db, utcnow


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(TITLE_MAX_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    # ---------- regras da entidade ----------

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    # ---------- serialização ----------

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "tags": self.tags.split(TAGS_SEPARATOR) if self.tags else [],
        }

    def to_dict_with_overdue(self):
        data = self.to_dict()
        data["overdue"] = self.is_overdue()
        return data

    def to_list_dict(self):
        data = self.to_dict_with_overdue()
        data["user_name"] = self.user.name if self.user else None
        data["category_name"] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": str(self.created_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "overdue": self.is_overdue(),
        }

    # ---------- consultas ----------

    @staticmethod
    def _overdue_condition(now):
        return and_(
            Task.due_date.isnot(None),
            Task.due_date < now,
            Task.status.notin_(CLOSED_STATUSES),
        )

    @classmethod
    def get_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_all_with_relations(cls):
        return (
            cls.query.options(joinedload(cls.user), joinedload(cls.category))
            .order_by(cls.id)
            .all()
        )

    @classmethod
    def list_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).order_by(cls.id).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = cls.query
        if text:
            pattern = f"%{text}%"
            query = query.filter(or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.filter(cls.status == status)
        if priority is not None:
            query = query.filter(cls.priority == priority)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.order_by(cls.id).all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

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
        query = cls.query.filter(cls._overdue_condition(now))
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.count()

    @classmethod
    def list_overdue(cls, now):
        return cls.query.filter(cls._overdue_condition(now)).order_by(cls.id).all()

    @classmethod
    def count_high_priority(cls, user_id, max_priority):
        return cls.query.filter(cls.user_id == user_id, cls.priority <= max_priority).count()

    @classmethod
    def count_created_since(cls, since):
        return cls.query.filter(cls.created_at >= since).count()

    @classmethod
    def count_completed_since(cls, since):
        return cls.query.filter(cls.status == STATUS_DONE, cls.updated_at >= since).count()

    @classmethod
    def totals_by_user(cls):
        """{user_id: (total de tasks, tasks concluídas)} numa única consulta."""
        done_flag = case((cls.status == STATUS_DONE, 1), else_=0)
        rows = (
            db.session.query(cls.user_id, func.count(cls.id), func.sum(done_flag))
            .group_by(cls.user_id)
            .all()
        )
        return {user_id: (total, int(done or 0)) for user_id, total, done in rows}

    @classmethod
    def count_by_category(cls):
        return dict(
            db.session.query(cls.category_id, func.count(cls.id)).group_by(cls.category_id).all()
        )

    @classmethod
    def delete_by_user(cls, user_id):
        """Apaga as tasks do usuário sem commit (o controller controla a transação)."""
        cls.query.filter_by(user_id=user_id).delete(synchronize_session=False)
