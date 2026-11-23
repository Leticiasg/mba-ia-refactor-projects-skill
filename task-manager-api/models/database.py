from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Agora em UTC, sem fuso, no mesmo formato das datas já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def save(*instances):
    """Grava as instâncias numa única transação; desfaz tudo se falhar."""
    try:
        for instance in instances:
            db.session.add(instance)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def delete(*instances):
    """Apaga as instâncias numa única transação; desfaz tudo se falhar."""
    try:
        for instance in instances:
            db.session.delete(instance)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
