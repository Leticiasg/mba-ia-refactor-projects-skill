"""Acesso a dados da tabela produtos."""

COLUNAS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    return {coluna: row[coluna] for coluna in COLUNAS}


def listar(db):
    return [_to_dict(row) for row in db.execute("SELECT * FROM produtos").fetchall()]


def buscar_por_id(db, produto_id):
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _to_dict(row) if row else None


def buscar_por_ids(db, produto_ids):
    ids = list(set(produto_ids))
    if not ids:
        return {}
    marcadores = ",".join("?" for _ in ids)
    rows = db.execute(f"SELECT * FROM produtos WHERE id IN ({marcadores})", ids).fetchall()
    return {row["id"]: _to_dict(row) for row in rows}


def pesquisar(db, termo=None, categoria=None, preco_min=None, preco_max=None):
    query, params = "SELECT * FROM produtos WHERE 1=1", []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)
    return [_to_dict(row) for row in db.execute(query, params).fetchall()]


def contar(db):
    return db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]


def inserir(db, nome, descricao, preco, estoque, categoria):
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )


def remover(db, produto_id):
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(db, produto_id, quantidade):
    """Baixa o estoque só se houver saldo. Devolve False quando não havia estoque suficiente."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1
