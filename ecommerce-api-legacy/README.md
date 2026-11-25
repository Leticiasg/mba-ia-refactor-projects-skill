# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

As rotas administrativas (`GET /api/admin/financial-report` e `DELETE /api/users/:id`) exigem o header `X-Admin-Token` igual à variável de ambiente `ADMIN_TOKEN`. Sem `ADMIN_TOKEN` definido, essas rotas respondem 401. As demais variáveis estão em `.env.example`:

```bash
ADMIN_TOKEN=um-token-longo npm start
```

No checkout, um e-mail que já tem conta só é aceito com a senha (`pwd`) correta dessa conta.

## Estrutura

`src/app.js` (composition root) · `config/` (ambiente, constantes, logger) · `models/` (SQL e seed) · `controllers/` (casos de uso) · `services/` (gateway de pagamento) · `views/` (rotas Express) · `middlewares/` (erros e token de admin) · `utils/` (hash de senha).

Exemplos de requisições estão em `api.http`.
