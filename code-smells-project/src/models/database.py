import sqlite3
from pathlib import Path

from flask import current_app, g

from src.models import seed

SCHEMA_SQL = """
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


def connect(caminho):
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def connect_read_only(caminho):
    conexao = sqlite3.connect(Path(caminho).as_uri() + "?mode=ro", uri=True)
    conexao.row_factory = sqlite3.Row
    return conexao


def get_db():
    """Uma conexão por requisição, guardada em flask.g e fechada no teardown."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(exception=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    conexao = connect(app.config["DATABASE_PATH"])
    try:
        conexao.executescript(SCHEMA_SQL)
        with conexao:
            seed.popular_se_vazio(conexao)
            seed.migrar_senhas_em_texto(conexao)
    finally:
        conexao.close()
