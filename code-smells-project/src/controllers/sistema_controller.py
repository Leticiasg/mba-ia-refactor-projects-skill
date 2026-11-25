"""Informações da API e health check."""
from src.config.settings import API_VERSION
from src.models import admin_model

ENDPOINTS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


def index():
    return {"mensagem": "Bem-vindo à API da Loja", "versao": API_VERSION, "endpoints": ENDPOINTS}


def health(db, ambiente):
    return {
        "status": "ok",
        "database": "connected",
        "counts": admin_model.contagens(db),
        "versao": API_VERSION,
        "ambiente": ambiente,
    }
