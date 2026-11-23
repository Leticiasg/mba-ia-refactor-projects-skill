"""Configuração lida do ambiente (ou de um arquivo .env, se existir)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default='false'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    SECRET_KEY_FROM_ENV = bool(os.environ.get('SECRET_KEY'))
    # Sem SECRET_KEY no ambiente, gera uma chave aleatória a cada boot (os tokens emitidos
    # deixam de valer ao reiniciar). O aviso é registrado em create_app().
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # Caminho relativo: o Flask-SQLAlchemy cria o arquivo em instance/tasks.db, como antes.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _env_bool('FLASK_DEBUG')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5000'))
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', str(8 * 60 * 60)))

    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_SENDER = os.environ.get('SMTP_SENDER', '') or SMTP_USER
