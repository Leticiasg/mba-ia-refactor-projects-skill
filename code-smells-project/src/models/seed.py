"""Dados de exemplo gravados no primeiro boot (tabela produtos vazia)."""
import logging

from src.models import produto_model, usuario_model

logger = logging.getLogger(__name__)

PRODUTOS = [
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

USUARIOS = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


def seed_if_empty(db):
    if produto_model.contar(db) > 0:
        return
    with db:
        for nome, descricao, preco, estoque, categoria in PRODUTOS:
            produto_model.inserir(db, nome, descricao, preco, estoque, categoria)
        for nome, email, senha, tipo in USUARIOS:
            usuario_model.inserir(db, nome, email, senha, tipo)
    logger.info("Seed aplicado: %d produtos, %d usuários", len(PRODUTOS), len(USUARIOS))


def migrar_senhas_legadas(db):
    """Converte senhas gravadas em texto puro (bancos criados pela versão antiga) para hash."""
    migradas = usuario_model.migrar_senhas_sem_hash(db)
    if migradas:
        logger.info("%d senha(s) em texto puro convertidas para hash", migradas)
