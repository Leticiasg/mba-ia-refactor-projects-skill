"""Constantes de domínio usadas por models e controllers."""

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
# Tasks nesses status nunca contam como atrasadas.
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)
DEFAULT_STATUS = STATUS_PENDING

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como "alta" no relatório do usuário
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
DATE_FORMAT = '%Y-%m-%d'

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER
PASSWORD_MIN_LENGTH = 4
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

DEFAULT_CATEGORY_COLOR = '#000000'
COLOR_PATTERN = r'^#[0-9a-fA-F]{6}$'

RECENT_ACTIVITY_DAYS = 7
