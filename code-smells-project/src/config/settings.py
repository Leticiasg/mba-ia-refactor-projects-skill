import os
import secrets
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolver_caminho(caminho):
    path = Path(caminho)
    return str(path if path.is_absolute() else PROJECT_ROOT / path)


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SECRET_KEY_FROM_ENV = bool(os.environ.get("SECRET_KEY"))
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = _resolver_caminho(os.environ.get("DATABASE_PATH", "loja.db"))
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    APP_ENV = os.environ.get("APP_ENV", "producao")


API_VERSION = "1.0.0"

# Produtos
CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# Usuários
TIPO_USUARIO_PADRAO = "cliente"

# Pedidos
STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]

# Relatório de vendas: (faturamento acima de, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
