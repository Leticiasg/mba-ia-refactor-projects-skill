"""Dados de exemplo gravados no primeiro boot (banco vazio)."""
import logging
import secrets

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

PRODUTOS_INICIAIS = [
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

# Clientes de demonstração (sem privilégio). A senha do admin vem do ambiente.
CLIENTES_DEMO = [
    ("João Silva", "joao@email.com", "123456"),
    ("Maria Santos", "maria@email.com", "senha123"),
]
ADMIN_DEMO = ("Admin", "admin@loja.com")


def seed_if_empty(conn, admin_password=None):
    """Grava os dados de exemplo se não houver produtos. Devolve True se gravou."""
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return False

    if not admin_password:
        admin_password = secrets.token_urlsafe(24)
        logger.warning(
            "SEED_ADMIN_PASSWORD não definida: o usuário admin foi criado com senha aleatória "
            "e não poderá fazer login. Defina a variável e recrie o banco para usá-lo."
        )

    usuarios = [(ADMIN_DEMO[0], ADMIN_DEMO[1], generate_password_hash(admin_password), "admin")]
    usuarios += [(nome, email, generate_password_hash(senha), "cliente") for nome, email, senha in CLIENTES_DEMO]

    with conn:
        conn.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_INICIAIS,
        )
        conn.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            usuarios,
        )
    logger.info("Banco populado com dados de exemplo")
    return True
