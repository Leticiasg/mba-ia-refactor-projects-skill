"""Operações administrativas e de sistema sobre o banco."""


def contagens(db):
    row = db.execute(
        "SELECT (SELECT COUNT(*) FROM produtos) AS produtos, "
        "(SELECT COUNT(*) FROM usuarios) AS usuarios, "
        "(SELECT COUNT(*) FROM pedidos) AS pedidos"
    ).fetchone()
    return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}


def resetar(db):
    with db:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            db.execute(f"DELETE FROM {tabela}")  # nomes fixos, sem entrada externa


def executar_consulta(readonly_db, sql):
    """Executa uma consulta numa conexão somente leitura."""
    return [dict(row) for row in readonly_db.execute(sql).fetchall()]
