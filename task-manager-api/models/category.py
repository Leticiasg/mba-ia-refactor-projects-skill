from sqlalchemy import func

from config.constants import DEFAULT_CATEGORY_COLOR
from models.database import db, utcnow


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

    @classmethod
    def get(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def count_all(cls):
        return db.session.query(func.count(cls.id)).scalar()

    @classmethod
    def list_with_task_counts(cls):
        """Lista (categoria, quantidade de tasks) numa consulta só."""
        from models.task import Task

        return (db.session.query(cls, func.count(Task.id))
                .outerjoin(Task, Task.category_id == cls.id)
                .group_by(cls.id)
                .order_by(cls.id)
                .all())

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
