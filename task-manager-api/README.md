# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` recria o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo.

## Configuração

As variáveis ficam em `.env.example` (copie para `.env`). Sem `SECRET_KEY`, a aplicação gera uma chave temporária a cada boot e os tokens de login deixam de valer ao reiniciar. O modo debug fica desligado, a menos que `FLASK_DEBUG=true`. Notificações por e-mail só são enviadas com as variáveis `SMTP_*` preenchidas.

## Estrutura

| Pasta | Camada |
|---|---|
| `app.py` | Entry point e composition root (`create_app()`) |
| `config/` | Configuração (ambiente) e constantes de domínio |
| `models/` | Entidades SQLAlchemy, consultas e regras da entidade |
| `controllers/` | Casos de uso, validação e permissões |
| `routes/` | View: blueprints que só recebem e respondem |
| `services/` | Integração externa (e-mail) |
| `middlewares/` | Erros de domínio, handler central e autenticação |

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o como `Authorization: Bearer <token>` em:

- `PUT /users/<id>` e `DELETE /users/<id>`: só o próprio usuário ou um admin; `role` e `active` só admin;
- `POST /users` com `role` diferente de `user`: só admin;
- `DELETE /tasks/<id>`: dono da task ou admin;
- `DELETE /categories/<id>`: só admin.

Usuários do seed: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd`, `pedro@email.com` / `pass`.
