from config.constants import DEFAULT_COLOR
from controllers import validators
from middlewares.errors import NotFoundError
from models.category import Category
from models.database import db, transaction
from models.task import Task


def _get_category_or_404(category_id):
    category = Category.get_by_id(category_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada")
    return category


def list_categories():
    task_counts = Task.count_by_category()
    result = []
    for category in Category.list_all():
        data = category.to_dict()
        data["task_count"] = task_counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    validators.require_body(data)
    name = validators.validate_required_text(data.get("name"), "Nome é obrigatório")
    category = Category(
        name=name,
        description=data.get("description", ""),
        color=validators.validate_color(data.get("color", DEFAULT_COLOR)),
    )
    with transaction("Erro ao criar categoria"):
        db.session.add(category)
    return category.to_dict()


def update_category(category_id, data):
    category = _get_category_or_404(category_id)
    validators.require_body(data)

    changes = {}
    if "name" in data:
        changes["name"] = validators.validate_required_text(data["name"], "Nome é obrigatório")
    if "description" in data:
        changes["description"] = data["description"]
    if "color" in data:
        changes["color"] = validators.validate_color(data["color"])

    with transaction("Erro ao atualizar"):
        for field, value in changes.items():
            setattr(category, field, value)
    return category.to_dict()


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    with transaction("Erro ao deletar"):
        db.session.delete(category)
