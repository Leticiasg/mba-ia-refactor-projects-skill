"""Acesso a dados da tabela usuarios. A senha nunca sai deste módulo."""
from werkzeug.security import check_password_hash, generate_password_hash

COLUNAS_PUBLICAS = ("id", "nome", "email", "tipo", "criado_em")
PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def _to_dict(row):
    return {coluna: row[coluna] for coluna in COLUNAS_PUBLICAS}


def listar(db):
    rows = db.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(db, usuario_id):
    row = db.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    return _to_dict(row) if row else None


def autenticar(db, email, senha):
    rows = db.execute("SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)).fetchall()
    for row in rows:
        if row["senha"] and check_password_hash(row["senha"], senha):
            return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None


def inserir(db, nome, email, senha, tipo):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    return cursor.lastrowid


def contar(db):
    return db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]


def migrar_senhas_sem_hash(db):
    rows = db.execute("SELECT id, senha FROM usuarios WHERE senha IS NOT NULL").fetchall()
    legadas = [row for row in rows if not row["senha"].startswith(PREFIXOS_HASH)]
    with db:
        for row in legadas:
            db.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(row["senha"]), row["id"])
            )
    return len(legadas)
