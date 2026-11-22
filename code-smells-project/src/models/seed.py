"""Dados de exemplo gravados no primeiro boot (mesmos do projeto original)."""
import logging

from src.models import usuario_model

logger = logging.getLogger(__name__)

PRODUTOS_EXEMPLO = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Contas de demonstração. As senhas são gravadas apenas como hash.
USUARIOS_EXEMPLO = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


def popular_se_vazio(conexao):
    total_produtos = conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    if total_produtos:
        return
    conexao.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        PRODUTOS_EXEMPLO,
    )
    for nome, email, senha, tipo in USUARIOS_EXEMPLO:
        usuario_model.criar(conexao, nome, email, usuario_model.gerar_hash_senha(senha), tipo)
    logger.info("Banco populado com dados de exemplo")


def migrar_senhas_em_texto(conexao):
    """Converte para hash senhas gravadas em texto puro por versões anteriores da aplicação."""
    linhas = conexao.execute("SELECT id, senha FROM usuarios").fetchall()
    migradas = 0
    for linha in linhas:
        if linha["senha"] and not usuario_model.eh_hash_senha(linha["senha"]):
            usuario_model.atualizar_senha(conexao, linha["id"], usuario_model.gerar_hash_senha(linha["senha"]))
            migradas += 1
    if migradas:
        logger.info("%d senha(s) em texto puro convertida(s) para hash", migradas)
