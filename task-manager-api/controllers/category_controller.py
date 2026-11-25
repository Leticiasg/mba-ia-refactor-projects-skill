from config.constants import DEFAULT_CATEGORY_COLOR
from controllers import permissions, validators
from middlewares.errors import NotFoundError, ValidationError
from models.category import Category
from models.database import db
from models.task import Task


def _get_category_or_404(category_id):
    category = Category.get(category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    result = []
    for category, task_count in Category.list_with_task_counts():
        data = category.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result


def create_category(data, requester):
    permissions.ensure_admin(requester)
    data = validators.require_body(data)
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')

    category = Category(
        name=validators.validate_name(name),
        description=data.get('description', ''),
        color=validators.validate_color(data.get('color', DEFAULT_CATEGORY_COLOR)),
    )
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(category_id, data, requester):
    permissions.ensure_admin(requester)
    category = _get_category_or_404(category_id)
    data = validators.require_body(data)

    if 'name' in data:
        category.name = validators.validate_name(data['name'])
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = validators.validate_color(data['color'])

    db.session.commit()
    return category.to_dict()


def delete_category(category_id, requester):
    permissions.ensure_admin(requester)
    category = _get_category_or_404(category_id)
    # Tasks da categoria ficam sem categoria, na mesma transação.
    Task.clear_category(category_id)
    db.session.delete(category)
    db.session.commit()
