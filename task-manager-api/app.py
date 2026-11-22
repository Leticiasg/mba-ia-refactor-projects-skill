"""Composition root: cria a app, carrega config, inicializa o banco e registra rotas e handlers."""
import logging
import os

from flask import Flask
from flask_cors import CORS

from config.settings import SECRET_KEY_FROM_ENV, Settings
from middlewares.error_handler import register_error_handlers
from models.database import db
from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Flask(__name__)
    app.config.from_object(settings)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        # Mesmo arquivo da versão original: instance/tasks.db ao lado deste módulo.
        os.makedirs(app.instance_path, exist_ok=True)
        db_path = os.path.join(app.instance_path, "tasks.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    if not SECRET_KEY_FROM_ENV:
        logger.warning("SECRET_KEY não definida; usando chave aleatória (tokens expiram a cada reinício).")

    CORS(app)
    db.init_app(app)

    for blueprint in (health_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    # As tabelas já estão registradas: as rotas importam os controllers, que importam os models.
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
