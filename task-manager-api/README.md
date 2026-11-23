# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

As variáveis ficam em `.env.example` (copie para `.env`). Sem `SECRET_KEY`, a app gera uma chave aleatória a cada boot, e os tokens emitidos deixam de valer ao reiniciar. O modo debug fica desligado, a menos que `FLASK_DEBUG=true`. O e-mail de notificação só é enviado se as variáveis `SMTP_*` estiverem definidas.

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o como `Authorization: Bearer <token>`. Um token de usuário `admin` é exigido para:

- `POST /users` com `"role": "admin"` (o cadastro comum continua aberto);
- `PUT /users/<id>` que altere `role` ou `active`;
- `DELETE /users/<id>`.

Sem token ou com token inválido a resposta é `401`; com token de quem não é admin, `403`.

## Estrutura

```
app.py          composition root (create_app) e entry point
config/         settings (ambiente) e constants (regras de domínio)
routes/         camada HTTP (views): lê a entrada e devolve o JSON
controllers/    casos de uso: validação, regras e transações
models/         ORM, consultas e serialização
middlewares/    erros de domínio, error handler central e autenticação
services/       integração externa (e-mail SMTP)
utils/          funções puras auxiliares
```
