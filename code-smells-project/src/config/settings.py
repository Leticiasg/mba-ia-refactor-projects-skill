"""Configuração lida do ambiente e constantes de domínio."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


SECRET_KEY_FROM_ENV = bool(os.environ.get("SECRET_KEY"))


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("FLASK_DEBUG")
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "loja.db"))
    TOKEN_MAX_AGE_SECONDS = int(os.environ.get("TOKEN_MAX_AGE_SECONDS", str(8 * 60 * 60)))
    AMBIENTE = os.environ.get("APP_ENV", "producao")
    SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD")


API_VERSION = "1.0.0"

TIPO_ADMIN = "admin"
TIPO_CLIENTE = "cliente"

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]
# Status que o próprio dono do pedido pode aplicar; os demais exigem admin.
STATUS_PERMITIDOS_AO_DONO = [STATUS_CANCELADO]

# (faturamento mínimo exclusivo, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
