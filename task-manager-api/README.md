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

As variáveis de ambiente estão em `.env.example` (copie para `.env`). Sem `SECRET_KEY`, a aplicação gera uma chave aleatória a cada boot e os tokens deixam de valer ao reiniciar. O modo debug fica desligado, a menos que `FLASK_DEBUG=true`.

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o como `Authorization: Bearer <token>` nas rotas que gravam dados:

- `POST /tasks`: qualquer usuário logado; usuário comum só cria tasks para si, admin atribui a qualquer um.
- `PUT` e `DELETE /tasks/<id>`: dono da task ou admin.
- `PUT` e `DELETE /users/<id>`: o próprio usuário ou admin; `role` e `active` só admin.
- `POST /users`: aberto para cadastro com role `user`; outros roles exigem admin.
- `POST`, `PUT` e `DELETE /categories`: só admin.

Estrutura: `routes/` (camada HTTP), `controllers/` (regras e validação), `models/` (ORM e consultas), `services/` (e-mail), `middlewares/` (auth e erros), `config/` (settings e constantes).
