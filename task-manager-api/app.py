"""Entry point e composition root: cria a app, liga config, banco, rotas e erros."""
import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  registra as tabelas antes do create_all
from config.settings import Settings
from middlewares.error_handler import register_error_handlers
from models.database import db
from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    if not settings.SECRET_KEY_FROM_ENV:
        logger.warning('SECRET_KEY não definida; usando chave aleatória temporária (tokens não sobrevivem ao reinício).')

    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)
    app.extensions['notification_service'] = NotificationService.from_config(app.config)

    for blueprint in (health_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
