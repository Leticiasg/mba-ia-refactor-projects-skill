from flask import Blueprint

from models.database import utcnow

health_bp = Blueprint('health', __name__)

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


@health_bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(utcnow())}


@health_bp.route('/')
def index():
    return {'message': API_NAME, 'version': API_VERSION}
