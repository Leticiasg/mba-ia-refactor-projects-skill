"""Casos de uso de produtos."""
import logging

from src.config.settings import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from src.middlewares.errors import NotFoundError, ValidationError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _is_number(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar_produto(dados):
    """Valida o corpo de criação/atualização e devolve os campos normalizados."""
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser inteiro")
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

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def _parse_preco_filtro(valor, campo):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{campo} deve ser numérico")


def listar(db):
    produtos = produto_model.listar(db)
    logger.info("Listando %d produtos", len(produtos))
    return produtos


def buscar(db, produto_id):
    produto = produto_model.buscar_por_id(db, produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado", sucesso=False)
    return produto


def pesquisar(db, termo, categoria, preco_min, preco_max):
    return produto_model.pesquisar(
        db,
        termo=termo,
        categoria=categoria,
        preco_min=_parse_preco_filtro(preco_min, "preco_min"),
        preco_max=_parse_preco_filtro(preco_max, "preco_max"),
    )


def criar(db, dados):
    campos = _validar_produto(dados)
    produto_id = produto_model.inserir(db, **campos)
    logger.info("Produto criado com ID %s", produto_id)
    return produto_id


def atualizar(db, produto_id, dados):
    if produto_model.buscar_por_id(db, produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    campos = _validar_produto(dados)
    produto_model.atualizar(db, produto_id, **campos)


def deletar(db, produto_id):
    if produto_model.buscar_por_id(db, produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(db, produto_id)
    logger.info("Produto %s deletado", produto_id)
