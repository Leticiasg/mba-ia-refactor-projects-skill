"""Configuração lida do ambiente (ou de um arquivo .env local)."""
import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _env_bool(name, default='false'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = _env_bool('FLASK_DEBUG')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5000'))

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AUTH_TOKEN_MAX_AGE_SECONDS = int(os.environ.get('AUTH_TOKEN_MAX_AGE_SECONDS', '86400'))

    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_SENDER = os.environ.get('SMTP_SENDER', '')


def warn_about_missing_secrets():
    if not os.environ.get('SECRET_KEY'):
        logger.warning('SECRET_KEY não definida; usando chave aleatória temporária '
                       '(os tokens de login deixam de valer quando a aplicação reinicia).')
