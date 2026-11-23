"""Composition root: cria a app Flask, carrega config, inicializa o banco e registra rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings, avisos_de_configuracao
from src.middlewares.error_handler import register_error_handlers
from src.models import database
from src.views.admin_routes import admin_bp
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.sistema_routes import sistema_bp
from src.views.usuario_routes import usuario_bp


def create_app(config_object=Settings):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    avisos_de_configuracao()

    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app)

    database.init_app(app)
    register_error_handlers(app)
    for blueprint in (sistema_bp, produto_bp, usuario_bp, pedido_bp, relatorio_bp, admin_bp):
        app.register_blueprint(blueprint)
    return app
