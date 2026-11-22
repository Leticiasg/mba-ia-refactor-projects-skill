_SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""
_ORDENACAO = " ORDER BY p.id, i.id"


def _agrupar_pedidos(linhas):
    pedidos = {}
    for linha in linhas:
        pedido = pedidos.setdefault(linha["id"], {
            "id": linha["id"],
            "usuario_id": linha["usuario_id"],
            "status": linha["status"],
            "total": linha["total"],
            "criado_em": linha["criado_em"],
            "itens": [],
        })
        if linha["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": linha["produto_id"],
                "produto_nome": linha["produto_nome"] or "Desconhecido",
                "quantidade": linha["quantidade"],
                "preco_unitario": linha["preco_unitario"],
            })
    return list(pedidos.values())


def listar(db, usuario_id=None):
    if usuario_id is None:
        linhas = db.execute(_SELECT_PEDIDOS_COM_ITENS + _ORDENACAO).fetchall()
    else:
        linhas = db.execute(
            _SELECT_PEDIDOS_COM_ITENS + " WHERE p.usuario_id = ?" + _ORDENACAO, (usuario_id,)
        ).fetchall()
    return _agrupar_pedidos(linhas)


def existe(db, pedido_id):
    return db.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def inserir(db, usuario_id, status, total):
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, status, total),
    )
    return cursor.lastrowid


def inserir_item(db, pedido_id, produto_id, quantidade, preco_unitario):
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(db, pedido_id, status):
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def resumo_vendas(db, status_pendente, status_aprovado, status_cancelado):
    linha = db.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (status_pendente, status_aprovado, status_cancelado),
    ).fetchone()
    return dict(linha)
