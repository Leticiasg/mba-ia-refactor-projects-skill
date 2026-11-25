from middlewares.errors import ForbiddenError, UnauthorizedError


def ensure_authenticated(requester):
    if requester is None:
        raise UnauthorizedError('Não autorizado')


def ensure_admin(requester):
    ensure_authenticated(requester)
    if not requester.is_admin():
        raise ForbiddenError('Acesso restrito a administradores')


def ensure_owner_or_admin(requester, owner_id):
    ensure_authenticated(requester)
    if owner_id is None or requester.id != owner_id:
        if not requester.is_admin():
            raise ForbiddenError('Sem permissão para alterar este recurso')
