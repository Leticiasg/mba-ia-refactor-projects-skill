# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, já reorganizada em MVC (`src/`).

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

## Configuração

Variáveis de ambiente (veja `.env.example`); todas têm padrão seguro para desenvolvimento:

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | chave do Flask |
| `FLASK_DEBUG` | `false` | modo debug |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | endereço do servidor |
| `DATABASE_PATH` | `loja.db` | arquivo SQLite |
| `ADMIN_TOKEN` | vazio (rotas admin bloqueadas) | header `X-Admin-Token` exigido em `/admin/*` |
| `APP_ENV` | `producao` | campo `ambiente` do `/health` |

## Estrutura

```
app.py                 entry point (create_app + app.run)
src/app.py             composition root
src/config/            settings e constantes de domínio
src/models/            conexão por requisição, schema, seed e SQL parametrizado
src/controllers/       validação, regras e transações
src/views/             Blueprints (rotas HTTP)
src/services/          notificações (simuladas em log)
src/middlewares/       erros de domínio, error handler e autenticação admin
```
