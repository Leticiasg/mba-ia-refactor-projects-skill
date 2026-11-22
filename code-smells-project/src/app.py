import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.middlewares.error_handler import register_error_handlers
from src.models import database
from src.views.admin_routes import admin_bp
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.usuario_routes import usuario_bp

logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)
    if not settings.SECRET_KEY_FROM_ENV:
        logger.warning("SECRET_KEY não definida; usando chave aleatória temporária.")
    if not settings.ADMIN_TOKEN:
        logger.warning("ADMIN_TOKEN não definido; rotas /admin/* ficam bloqueadas.")

    CORS(app)
    database.init_app(app)

    for blueprint in (produto_bp, usuario_bp, pedido_bp, admin_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    return app
