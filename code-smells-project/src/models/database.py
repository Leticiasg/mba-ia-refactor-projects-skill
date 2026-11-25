"""Conexão SQLite por requisição e criação do schema."""
import sqlite3
from pathlib import Path

from flask import current_app, g

from src.models.seed import seed_if_empty

SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    descricao TEXT,
    preco REAL,
    estoque INTEGER,
    categoria TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    senha TEXT,
    tipo TEXT DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    status TEXT DEFAULT 'pendente',
    total REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER,
    produto_id INTEGER,
    quantidade INTEGER,
    preco_unitario REAL
);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def get_readonly_db():
    """Conexão somente leitura, usada pela consulta administrativa."""
    if "db_readonly" not in g:
        uri = Path(current_app.config["DATABASE_PATH"]).resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        g.db_readonly = conn
    return g.db_readonly


def close_db(exception=None):
    for key in ("db", "db_readonly"):
        conn = g.pop(key, None)
        if conn is not None:
            conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    conn = connect(app.config["DATABASE_PATH"])
    try:
        conn.executescript(SCHEMA)
        seed_if_empty(conn, app.config.get("SEED_ADMIN_PASSWORD"))
    finally:
        conn.close()
