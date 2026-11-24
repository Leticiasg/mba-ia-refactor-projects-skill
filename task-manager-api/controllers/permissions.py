from middlewares.errors import ForbiddenError, UnauthorizedError

FORBIDDEN_MESSAGE = 'Sem permissão'


def ensure_authenticated(requester):
    if requester is None:
        raise UnauthorizedError('Não autorizado')


def ensure_admin(requester):
    ensure_authenticated(requester)
    if not requester.is_admin():
        raise ForbiddenError(FORBIDDEN_MESSAGE)


def ensure_owner_or_admin(requester, owner_id):
    ensure_authenticated(requester)
    if requester.id != owner_id and not requester.is_admin():
        raise ForbiddenError(FORBIDDEN_MESSAGE)
