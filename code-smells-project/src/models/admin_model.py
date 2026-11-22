def resetar(db):
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    db.execute("DELETE FROM produtos")
    db.execute("DELETE FROM usuarios")


def executar_consulta_leitura(conexao_somente_leitura, sql):
    return [dict(linha) for linha in conexao_somente_leitura.execute(sql).fetchall()]


def contar_registros(db):
    linha = db.execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    ).fetchone()
    return dict(linha)
