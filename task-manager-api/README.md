# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, já reorganizada em camadas MVC.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo. **Rode-o antes do primeiro boot**, senão os endpoints retornam listas vazias.

## Configuração

As variáveis ficam em `.env.example`. Copie para `.env` e defina pelo menos `SECRET_KEY`. Sem ela, a app gera uma chave aleatória a cada boot e os tokens deixam de valer quando ela reinicia. O modo debug só liga com `FLASK_DEBUG=true`.

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o como `Authorization: Bearer <token>` (de um usuário admin) para:

- criar um usuário com `role: "admin"` em `POST /users`;
- mudar `role` ou `active` em `PUT /users/<id>`.

As demais rotas continuam públicas.

## Estrutura

```
app.py          composition root (create_app) e entry point
config/         settings (ambiente) e constantes de domínio
models/         SQLAlchemy: entidades, consultas e regras da entidade
controllers/    casos de uso e validação
routes/         blueprints HTTP (camada de view)
middlewares/    erros de domínio, error handler central e autenticação
```
