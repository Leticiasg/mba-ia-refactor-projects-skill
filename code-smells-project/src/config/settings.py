"""Configuração da aplicação: variáveis de ambiente e constantes de domínio."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _env_bool(nome, padrao="false"):
    return os.environ.get(nome, padrao).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("FLASK_DEBUG")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    AMBIENTE = os.environ.get("APP_ENV", "producao")


def avisos_de_configuracao():
    if not os.environ.get("SECRET_KEY"):
        logger.warning("SECRET_KEY não definida; usando chave aleatória temporária.")
    if not Settings.ADMIN_TOKEN:
        logger.warning("ADMIN_TOKEN não definido; rotas /admin ficam bloqueadas.")


# --- Constantes de domínio ---
API_VERSAO = "1.0.0"

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

TIPO_USUARIO_PADRAO = "cliente"

# (faturamento mínimo exclusivo, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
