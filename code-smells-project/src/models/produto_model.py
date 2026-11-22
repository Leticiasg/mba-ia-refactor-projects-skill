SELECT_PRODUTOS = "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos"


def listar(db):
    return [dict(linha) for linha in db.execute(SELECT_PRODUTOS).fetchall()]


def buscar_por_id(db, produto_id):
    linha = db.execute(SELECT_PRODUTOS + " WHERE id = ?", (produto_id,)).fetchone()
    return dict(linha) if linha else None


def buscar(db, termo, categoria=None, preco_min=None, preco_max=None):
    query = SELECT_PRODUTOS + " WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += ["%" + termo + "%", "%" + termo + "%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)
    return [dict(linha) for linha in db.execute(query, params).fetchall()]


def criar(db, nome, descricao, preco, estoque, categoria):
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


def deletar(db, produto_id):
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(db, produto_id, quantidade):
    """Baixa o estoque só se houver saldo. Devolve False quando não há estoque suficiente."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1
