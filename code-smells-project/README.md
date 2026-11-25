# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Variáveis de ambiente (veja `.env.example`): `SECRET_KEY`, `FLASK_DEBUG` (padrão `false`), `HOST` (padrão `127.0.0.1`), `PORT`, `DATABASE_PATH`, `TOKEN_MAX_AGE_SECONDS`, `APP_ENV` e `SEED_ADMIN_PASSWORD`.

- Sem `SECRET_KEY`, a app gera uma chave aleatória a cada boot (os tokens deixam de valer ao reiniciar).
- A senha do `admin@loja.com` vem de `SEED_ADMIN_PASSWORD` no momento em que o banco é criado. Sem ela, o admin recebe uma senha aleatória e não consegue entrar.

## Autenticação

`POST /login` devolve um campo `token`. Envie-o em `Authorization: Bearer <token>`.

| Rota | Quem pode |
|---|---|
| `POST/PUT/DELETE /produtos` | admin |
| `POST /pedidos` | usuário logado (para outro `usuario_id`, só admin) |
| `PUT /pedidos/<id>/status` | admin; o dono do pedido só pode cancelar |
| `POST /admin/reset-db`, `POST /admin/query` (só `SELECT`, conexão somente leitura) | admin |

## Estrutura

```
app.py              entry point (python app.py)
src/app.py          create_app(): config, banco, blueprints, error handler
src/config/         configuração do ambiente e constantes de domínio
src/models/         SQL parametrizado, schema e seed
src/controllers/    validação e regras de negócio
src/views/          blueprints (camada HTTP)
src/services/       notificações
src/middlewares/    autenticação e tratamento de erro
```
