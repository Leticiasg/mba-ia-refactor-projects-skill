"""Operações administrativas e de diagnóstico sobre o banco."""
from src.models.database import connect


def contagens(db):
    row = db.execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    ).fetchone()
    return dict(row)


def apagar_tudo(db):
    with db:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            db.execute(f"DELETE FROM {tabela}")  # nomes fixos, sem entrada do cliente


def executar_select_somente_leitura(database_path, sql):
    conn = connect(database_path, read_only=True)
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    finally:
        conn.close()
