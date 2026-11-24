from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Data/hora UTC sem fuso, no mesmo formato das datas já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
