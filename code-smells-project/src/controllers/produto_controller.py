import logging

from src.config.settings import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from src.middlewares.errors import NotFoundError, ValidationError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo, mensagem in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"),
                            ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not _numero(preco):
        raise ValidationError("Preço inválido")
    if not _numero(estoque):
        raise ValidationError("Estoque inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
    return nome, descricao, preco, estoque, categoria


def _parse_preco(valor, campo):
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{campo} inválido")


def listar(db):
    produtos = produto_model.listar(db)
    logger.info("Listando %d produtos", len(produtos))
    return produtos


def buscar(db, produto_id):
    produto = produto_model.buscar_por_id(db, produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado", extra={"sucesso": False})
    return produto


def pesquisar(db, termo, categoria, preco_min, preco_max):
    return produto_model.pesquisar(
        db, termo, categoria, _parse_preco(preco_min, "preco_min"), _parse_preco(preco_max, "preco_max")
    )


def criar(db, dados):
    campos = _validar(dados)
    with db:
        produto_id = produto_model.inserir(db, *campos)
    logger.info("Produto criado com ID: %s", produto_id)
    return produto_id


def atualizar(db, produto_id, dados):
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError("Produto não encontrado")
    campos = _validar(dados)
    with db:
        produto_model.atualizar(db, produto_id, *campos)


def remover(db, produto_id):
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError("Produto não encontrado")
    with db:
        produto_model.remover(db, produto_id)
    logger.info("Produto %s deletado", produto_id)
