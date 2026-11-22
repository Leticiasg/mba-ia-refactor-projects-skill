"""Configuração de ambiente. Segredos vêm de variáveis de ambiente (ou de um .env local)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


SECRET_KEY_FROM_ENV = bool(os.environ.get("SECRET_KEY"))


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("FLASK_DEBUG")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    # Vazio: usa instance/tasks.db, o mesmo arquivo da versão original.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TOKEN_MAX_AGE_SECONDS = int(os.environ.get("TOKEN_MAX_AGE_SECONDS", "28800"))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
