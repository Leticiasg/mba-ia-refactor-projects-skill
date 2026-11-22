from werkzeug.security import check_password_hash, generate_password_hash

_METODOS_HASH = ("scrypt", "pbkdf2")

SELECT_USUARIO_PUBLICO = "SELECT id, nome, email, tipo, criado_em FROM usuarios"


def gerar_hash_senha(senha):
    return generate_password_hash(senha)


def eh_hash_senha(valor):
    metodo = valor.split("$", 1)[0].split(":", 1)[0]
    return "$" in valor and metodo in _METODOS_HASH


def senha_confere(hash_senha, senha):
    return bool(hash_senha) and eh_hash_senha(hash_senha) and check_password_hash(hash_senha, senha)


def listar(db):
    return [dict(linha) for linha in db.execute(SELECT_USUARIO_PUBLICO).fetchall()]


def buscar_por_id(db, usuario_id):
    linha = db.execute(SELECT_USUARIO_PUBLICO + " WHERE id = ?", (usuario_id,)).fetchone()
    return dict(linha) if linha else None


def autenticar(db, email, senha):
    """Devolve o usuário (sem senha) se o e-mail e a senha conferem; senão None."""
    linhas = db.execute(
        "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
    ).fetchall()
    for linha in linhas:
        if senha_confere(linha["senha"], senha):
            return {"id": linha["id"], "nome": linha["nome"], "email": linha["email"], "tipo": linha["tipo"]}
    return None


def criar(db, nome, email, hash_senha, tipo):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, hash_senha, tipo),
    )
    return cursor.lastrowid


def atualizar_senha(db, usuario_id, hash_senha):
    db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (hash_senha, usuario_id))
