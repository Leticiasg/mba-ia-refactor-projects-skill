import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from middlewares.errors import DatabaseError

logger = logging.getLogger(__name__)

db = SQLAlchemy()


def utcnow():
    """UTC sem fuso, no mesmo formato das datas já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@contextmanager
def transaction(error_message):
    """Commit no fim; rollback e DatabaseError (500) se o banco falhar."""
    try:
        yield db.session
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        logger.exception("Falha no banco: %s", error_message)
        raise DatabaseError(error_message) from error
