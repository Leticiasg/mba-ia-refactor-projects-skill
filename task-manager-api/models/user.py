from sqlalchemy import case, func
from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import DEFAULT_ROLE, ROLE_ADMIN, STATUS_DONE
from models.database import db, utcnow
from models.task import Task


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        # O hash da senha nunca sai na resposta.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, plain_password):
        self.password = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        return check_password_hash(self.password, plain_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    # ---- consultas ----

    @staticmethod
    def get(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def count_all():
        return User.query.count()

    @staticmethod
    def list_with_task_counts():
        """[(user, task_count)] numa consulta só."""
        return (
            db.session.query(User, func.count(Task.id))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
            .all()
        )

    @staticmethod
    def productivity():
        """[(user_id, name, total, concluídas)] numa consulta só."""
        done_count = func.coalesce(func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0)
        return (
            db.session.query(User.id, User.name, func.count(Task.id), done_count)
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
            .all()
        )
