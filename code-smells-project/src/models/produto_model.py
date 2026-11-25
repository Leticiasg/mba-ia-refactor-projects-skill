"""Acesso a dados da tabela produtos."""

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def _to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar(db):
    rows = db.execute(f"SELECT {COLUNAS} FROM produtos").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(db, produto_id):
    row = db.execute(f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _to_dict(row) if row else None


def pesquisar(db, termo=None, categoria=None, preco_min=None, preco_max=None):
    query = f"SELECT {COLUNAS} FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)
    return [_to_dict(row) for row in db.execute(query, params).fetchall()]


def inserir(db, nome, descricao, preco, estoque, categoria):
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def deletar(db, produto_id):
    with db:
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(db, produto_id, quantidade):
    """Baixa o estoque só se houver saldo. Não faz commit: roda dentro da transação de quem chama."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1
