import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import DEFAULT_ROLE, ROLE_ADMIN
from models.database import db, utcnow

# Formato antigo (MD5 sem salt). Só é aceito para migrar o hash no próximo login.
_LEGACY_MD5_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def has_legacy_password_hash(self):
        return bool(self.password and _LEGACY_MD5_PATTERN.match(self.password))

    def check_password(self, raw_password):
        if self.has_legacy_password_hash():
            legacy_digest = hashlib.md5(raw_password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy_digest)
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def list_all(cls):
        return cls.query.order_by(cls.id).all()

    @classmethod
    def count_all(cls):
        return cls.query.count()
