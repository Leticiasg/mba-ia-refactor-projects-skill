import logging

from src.config.settings import TIPO_USUARIO_PADRAO
from src.middlewares.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models import usuario_model

logger = logging.getLogger(__name__)


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else ""


def listar(db):
    return usuario_model.listar(db)


def buscar(db, usuario_id):
    usuario = usuario_model.buscar_por_id(db, usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(db, dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), _texto(dados, "senha")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    with db:
        usuario_id = usuario_model.inserir(db, nome, email, senha, TIPO_USUARIO_PADRAO)
    logger.info("Usuário criado: id %s", usuario_id)
    return usuario_id


def login(db, dados):
    email, senha = _texto(dados, "email"), _texto(dados, "senha")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    usuario = usuario_model.autenticar(db, email, senha)
    if not usuario:
        logger.info("Login falhou")
        raise UnauthorizedError("Email ou senha inválidos", extra={"sucesso": False})
    logger.info("Login bem-sucedido: usuario %s", usuario["id"])
    return usuario
