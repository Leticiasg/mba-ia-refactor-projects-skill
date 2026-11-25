"""Acesso a dados das tabelas pedidos e itens_pedido."""

_SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar(db, usuario_id=None):
    query = _SELECT_PEDIDOS_COM_ITENS
    params = ()
    if usuario_id is not None:
        query += " WHERE p.usuario_id = ?"
        params = (usuario_id,)
    query += " ORDER BY p.id, i.id"
    return _agrupar(db.execute(query, params).fetchall())


def buscar_por_id(db, pedido_id):
    row = db.execute("SELECT id, usuario_id, status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return dict(row) if row else None


def inserir(db, usuario_id, status, total):
    """Não faz commit: roda dentro da transação de quem chama."""
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, status, total),
    )
    return cursor.lastrowid


def inserir_item(db, pedido_id, produto_id, quantidade, preco_unitario):
    """Não faz commit: roda dentro da transação de quem chama."""
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(db, pedido_id, status):
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def resumo_por_status(db):
    """Quantidade e soma de total por status, numa única consulta."""
    rows = db.execute(
        "SELECT status, COUNT(*) AS quantidade, COALESCE(SUM(total), 0) AS faturamento "
        "FROM pedidos GROUP BY status"
    ).fetchall()
    return {row["status"]: {"quantidade": row["quantidade"], "faturamento": row["faturamento"]} for row in rows}
