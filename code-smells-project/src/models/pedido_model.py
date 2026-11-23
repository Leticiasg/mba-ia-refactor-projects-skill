"""Acesso a dados de pedidos e itens_pedido."""

_SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def listar(db, usuario_id=None):
    query, params = _SELECT_PEDIDOS_COM_ITENS, []
    if usuario_id is not None:
        query += " WHERE p.usuario_id = ?"
        params.append(usuario_id)
    query += " ORDER BY p.id, i.id"

    pedidos = {}
    for row in db.execute(query, params).fetchall():
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_nome"] is not None else "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def inserir(db, usuario_id, status, total):
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)", (usuario_id, status, total)
    )
    return cursor.lastrowid


def inserir_item(db, pedido_id, produto_id, quantidade, preco_unitario):
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(db, pedido_id, status):
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def contar(db):
    return db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]


def resumo_vendas(db, status_pendente, status_aprovado, status_cancelado):
    row = db.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COUNT(CASE WHEN status = ? THEN 1 END) AS pendentes,
               COUNT(CASE WHEN status = ? THEN 1 END) AS aprovados,
               COUNT(CASE WHEN status = ? THEN 1 END) AS cancelados
        FROM pedidos
        """,
        (status_pendente, status_aprovado, status_cancelado),
    ).fetchone()
    return dict(row)
