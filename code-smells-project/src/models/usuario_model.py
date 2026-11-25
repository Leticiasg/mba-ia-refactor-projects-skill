"""Acesso a dados da tabela usuarios. A senha (hash) nunca sai nos dicionários públicos."""
from src.config.settings import TIPO_ADMIN

COLUNAS_PUBLICAS = "id, nome, email, tipo, criado_em"


def _to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def listar(db):
    rows = db.execute(f"SELECT {COLUNAS_PUBLICAS} FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(db, usuario_id):
    row = db.execute(f"SELECT {COLUNAS_PUBLICAS} FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def buscar_credenciais(db, email):
    """Uso interno do login: devolve id, nome, email, tipo e o hash da senha."""
    row = db.execute(
        "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ? ORDER BY id LIMIT 1",
        (email,),
    ).fetchone()
    return dict(row) if row else None


def email_existe(db, email):
    return db.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def inserir(db, nome, email, senha_hash, tipo):
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
    return cursor.lastrowid


def is_admin(usuario):
    return usuario is not None and usuario["tipo"] == TIPO_ADMIN
