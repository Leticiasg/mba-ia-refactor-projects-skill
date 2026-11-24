import hashlib
import hmac
import re

from sqlalchemy import case, func
from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import DEFAULT_ROLE, ROLE_ADMIN, STATUS_DONE
from models.database import db, utcnow

# Hashes gravados pela versão antiga (MD5 sem salt): só aceitos para migrar no login.
LEGACY_MD5_HASH = re.compile(r'^[0-9a-f]{32}$')


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
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    # ---- senha --------------------------------------------------------------

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def has_legacy_password_hash(self):
        return bool(self.password and LEGACY_MD5_HASH.match(self.password))

    def check_password(self, raw_password):
        if self.has_legacy_password_hash():
            legacy_digest = hashlib.md5(raw_password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy_digest)
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    # ---- consultas ----------------------------------------------------------

    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def count_all(cls):
        return db.session.query(func.count(cls.id)).scalar()

    @classmethod
    def list_with_task_counts(cls):
        """Lista (usuário, total de tasks) numa consulta só."""
        from models.task import Task

        return (db.session.query(cls, func.count(Task.id))
                .outerjoin(Task, Task.user_id == cls.id)
                .group_by(cls.id)
                .order_by(cls.id)
                .all())

    @classmethod
    def productivity_rows(cls):
        """Lista (id, nome, total de tasks, tasks concluídas) por usuário numa consulta só."""
        from models.task import Task

        done_flag = case((Task.status == STATUS_DONE, 1), else_=0)
        return (db.session.query(cls.id, cls.name, func.count(Task.id), func.coalesce(func.sum(done_flag), 0))
                .outerjoin(Task, Task.user_id == cls.id)
                .group_by(cls.id)
                .order_by(cls.id)
                .all())

    # ---- gravação -----------------------------------------------------------

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete_with_tasks(self):
        """Apaga o usuário e as tasks dele na mesma transação."""
        from models.task import Task

        try:
            Task.query.filter_by(user_id=self.id).delete(synchronize_session=False)
            db.session.delete(self)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
