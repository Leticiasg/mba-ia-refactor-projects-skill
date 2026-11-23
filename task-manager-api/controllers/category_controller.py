import logging
import re

from config.constants import COLOR_PATTERN, DEFAULT_CATEGORY_COLOR
from controllers.validators import require_payload
from middlewares.errors import NotFoundError, ValidationError
from models import category as category_model
from models.category import Category
from models.database import delete, save

logger = logging.getLogger(__name__)

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


def _validate_name(name):
    if not isinstance(name, str) or not name:
        raise ValidationError('Nome é obrigatório')
    return name


def _validate_color(color):
    if not isinstance(color, str) or not re.match(COLOR_PATTERN, color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


def list_categories():
    return category_model.list_with_task_counts()


def get_category(category_id):
    category = category_model.get_by_id(category_id)
    if category is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)
    return category


def create_category(data):
    require_payload(data)
    category = Category(
        name=_validate_name(data.get('name')),
        description=data.get('description', ''),
        color=_validate_color(data.get('color', DEFAULT_CATEGORY_COLOR)),
    )
    save(category)
    logger.info('Categoria criada: %s', category.id)
    return category


def update_category(category_id, data):
    category = get_category(category_id)
    require_payload(data, allow_empty=True)  # {} é aceito e não muda nada, como antes
    if 'name' in data:
        _validate_name(data['name'])
    if 'color' in data:
        _validate_color(data['color'])

    for field in ('name', 'description', 'color'):
        if field in data:
            setattr(category, field, data[field])
    save(category)
    return category


def delete_category(category_id):
    category = get_category(category_id)
    delete(category)
    logger.info('Categoria deletada: %s', category_id)
