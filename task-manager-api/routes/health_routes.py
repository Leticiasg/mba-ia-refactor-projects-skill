from datetime import datetime

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': str(datetime.now())})


@health_bp.route('/')
def index():
    return jsonify({'message': 'Task Manager API', 'version': '1.0'})
