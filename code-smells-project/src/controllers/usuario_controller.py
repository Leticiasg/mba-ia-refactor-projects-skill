"""Casos de uso de usuários e login."""
import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.config.settings import TIPO_CLIENTE
from src.middlewares.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models import usuario_model

logger = logging.getLogger(__name__)


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor.strip() if isinstance(valor, str) else ""


def listar(db):
    return usuario_model.listar(db)


def buscar(db, usuario_id):
    usuario = usuario_model.buscar_por_id(db, usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(db, dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    nome = _texto(dados, "nome")
    email = _texto(dados, "email")
    senha = dados.get("senha", "")
    if not nome or not email or not isinstance(senha, str) or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if usuario_model.email_existe(db, email):
        raise ValidationError("Email já cadastrado")

    # Cadastro público sempre cria cliente; o tipo não vem do corpo.
    usuario_id = usuario_model.inserir(db, nome, email, generate_password_hash(senha), TIPO_CLIENTE)
    logger.info("Usuário %s criado", usuario_id)
    return usuario_id


def autenticar(db, dados):
    email = _texto(dados, "email")
    senha = dados.get("senha", "")
    if not email or not isinstance(senha, str) or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    credenciais = usuario_model.buscar_credenciais(db, email)
    if credenciais is None or not check_password_hash(credenciais["senha"], senha):
        logger.info("Falha de login")
        raise UnauthorizedError("Email ou senha inválidos", sucesso=False)

    logger.info("Login bem-sucedido do usuário %s", credenciais["id"])
    return {
        "id": credenciais["id"],
        "nome": credenciais["nome"],
        "email": credenciais["email"],
        "tipo": credenciais["tipo"],
    }
