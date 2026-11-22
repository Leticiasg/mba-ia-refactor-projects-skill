# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`, na raiz do projeto) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Variáveis de ambiente (veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | chave do Flask |
| `ADMIN_TOKEN` | vazio (rotas admin bloqueadas) | enviado no header `X-Admin-Token` para `/admin/*` |
| `FLASK_DEBUG` | `false` | modo debug |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | endereço do servidor |
| `DATABASE_PATH` | `loja.db` | arquivo SQLite (relativo à raiz do projeto) |
| `APP_ENV` | `producao` | valor exibido em `/health` |

## Estrutura

```
app.py              entry point (python app.py)
src/app.py          create_app(): config, banco, blueprints, handlers de erro
src/config/         settings e constantes de domínio
src/models/         acesso a dados (SQL parametrizado), schema e seed
src/controllers/    casos de uso, validação, regras de negócio
src/views/          rotas (Blueprints)
src/services/       notificações
src/middlewares/    erros de domínio, handler central, autenticação admin
```
