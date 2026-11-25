from sqlalchemy import func

from config.constants import DEFAULT_CATEGORY_COLOR
from models.database import db, utcnow
from models.task import Task


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_CATEGORY_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    # ---- consultas ----

    @staticmethod
    def get(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def count_all():
        return Category.query.count()

    @staticmethod
    def list_with_task_counts():
        """[(category, task_count)] numa consulta só."""
        return (
            db.session.query(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.id)
            .all()
        )
