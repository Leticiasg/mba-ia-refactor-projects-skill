import logging

from config.constants import DEFAULT_CATEGORY_COLOR
from controllers import validators
from controllers.permissions import ensure_admin
from middlewares.errors import NotFoundError
from models.category import Category

logger = logging.getLogger(__name__)

CATEGORY_NOT_FOUND = 'Categoria não encontrada'
NAME_REQUIRED = 'Nome é obrigatório'


def _get_category_or_404(category_id):
    category = Category.get(category_id)
    if category is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)
    return category


def list_categories():
    result = []
    for category, task_count in Category.list_with_task_counts():
        data = category.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result


def create_category(data):
    validators.require_body(data)
    category = Category(
        name=validators.validate_required_text(data.get('name'), NAME_REQUIRED),
        description=data.get('description', ''),
        color=validators.validate_color(data.get('color', DEFAULT_CATEGORY_COLOR)),
    )
    category.save()
    logger.info('Categoria criada: %s', category.id)
    return category.to_dict()


def update_category(category_id, data):
    category = _get_category_or_404(category_id)
    validators.require_body(data)
    if 'name' in data:
        category.name = validators.validate_required_text(data['name'], NAME_REQUIRED)
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = validators.validate_color(data['color'])
    category.save()
    return category.to_dict()


def delete_category(category_id, requester):
    ensure_admin(requester)
    category = _get_category_or_404(category_id)
    category.delete()
    logger.info('Categoria deletada: %s', category_id)
