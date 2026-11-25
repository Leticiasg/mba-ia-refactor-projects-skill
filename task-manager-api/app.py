"""Composition root: cria a app, carrega config, liga banco, rotas, serviços e tratamento de erro."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from middlewares.error_handler import register_error_handlers
from models import db
from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)

    CORS(app)
    db.init_app(app)
    app.extensions['notification_service'] = NotificationService.from_config(app.config)

    for blueprint in (health_bp, task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
