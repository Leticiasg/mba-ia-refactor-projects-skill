# Análise de projeto (Fase 1)

Heurísticas para descobrir a stack, o banco, as rotas e a arquitetura atual de um projeto backend. Toda conclusão precisa de uma evidência concreta: um arquivo, um import ou uma linha de código. Se não houver evidência, escreva "não detectado" em vez de supor.

## 1. Arquivos a ignorar

Nunca conte nem audite:

- dependências instaladas: `node_modules/`, `.venv/`, `venv/`, `env/`, `vendor/`
- artefatos: `__pycache__/`, `*.pyc`, `dist/`, `build/`, `coverage/`
- controle e ferramentas: `.git/`, `.claude/`, `.idea/`, `.vscode/`
- dados e travas: `*.db`, `*.sqlite`, `instance/`, `package-lock.json`, `yarn.lock`, `poetry.lock`

## 2. Linguagem

| Evidência | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, arquivos `*.py` | Python |
| `package.json` e arquivos `*.js` / `*.mjs` / `*.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` ou arquivos `*.ts` | TypeScript (Node.js) |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java / Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# |

Se houver mais de uma, a linguagem principal é a do entry point (seção 5).

## 3. Framework e versão

Procure primeiro no arquivo de dependências e confirme pelos imports.

| Framework | Dependência | Import / uso no código |
|---|---|---|
| Flask | `flask` | `from flask import Flask`, `Flask(__name__)`, `Blueprint(` |
| FastAPI | `fastapi` | `FastAPI()`, `APIRouter(` |
| Django | `django` | `manage.py`, `settings.py`, `urls.py` |
| Express | `express` | `require('express')`, `express()`, `express.Router()` |
| Fastify | `fastify` | `require('fastify')` |
| NestJS | `@nestjs/core` | decorators `@Controller(` |

Versão: use a versão fixada no arquivo de dependências (`flask==3.1.1`). Se for uma faixa (`^4.18.2`), confirme a versão instalada no lockfile ou em `node_modules/<pacote>/package.json` e informe as duas.

Liste as demais dependências de runtime (ex.: `flask-cors`, `sqlite3`, `marshmallow`). Ignore as de desenvolvimento.

## 4. Banco de dados

| Evidência | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite com SQL cru (Python) |
| `require('sqlite3')`, `new sqlite3.Database(` | SQLite com SQL cru (Node) |
| `':memory:'` no lugar do caminho | SQLite em memória: os dados somem a cada reinício |
| `SQLALCHEMY_DATABASE_URI`, `db.Model`, `flask_sqlalchemy` | ORM SQLAlchemy |
| `mongoose`, `MongoClient` | MongoDB |
| `pg`, `psycopg2`, `postgresql://` | PostgreSQL |
| `prisma`, `sequelize`, `typeorm` | ORM Node |

Tabelas: procure `CREATE TABLE` (SQL cru) ou classes de modelo (`class X(db.Model)`, `__tablename__`). Liste os nomes.

Arquivo do banco: anote o caminho. No Flask-SQLAlchemy, `sqlite:///arquivo.db` relativo fica em `instance/` ao lado do módulo da app. Isso importa na Fase 3: mover a app de pasta muda onde o banco é criado.

## 5. Entry point, porta e como rodar

| Stack | Sinais |
|---|---|
| Python/Flask | `if __name__ == "__main__":`, `app.run(`; a porta está em `port=` (padrão 5000) |
| Node/Express | `"main"` e `"scripts.start"` no `package.json`; `app.listen(` |

Descubra também, porque a Fase 3 vai precisar:

- o comando de instalação (`pip install -r requirements.txt`, `npm install`);
- o comando para subir (`python app.py`, `npm start`), lido do README do projeto ou do `package.json`;
- scripts de carga de dados que precisam rodar antes do boot (`seed.py`, `"scripts.seed"`, instruções no README);
- variáveis de ambiente lidas no código (`os.environ`, `os.getenv`, `process.env`).

## 6. Inventário de rotas

Liste todas as rotas com método, caminho e `arquivo:linha` do handler. A Fase 3 usa essa lista para validar.

| Stack | O que procurar |
|---|---|
| Flask | `@app.route(`, `@<bp>.route(`, `app.add_url_rule(`, o argumento `methods=[...]` (sem ele, é GET) e `register_blueprint(..., url_prefix=...)` (o prefixo entra no caminho) |
| Express | `app.get/post/put/patch/delete(`, `router.<método>(`, `app.use('/prefixo', router)` |

Para cada rota, anote também o que ela espera no corpo ou na query string (os campos lidos de `request.get_json()`, `request.args`, `req.body`, `req.query`, `req.params`). Arquivos de exemplo como `*.http`, coleções Postman ou o README costumam trazer requisições prontas: use-as.

## 7. Domínio

Deduza o domínio pelos nomes de tabelas, rotas e entidades. Exemplos: `produtos`, `pedidos`, `usuarios` indicam e-commerce; `courses`, `enrollments`, `payments` indicam LMS com checkout; `tasks`, `categories`, `users` indicam gerenciador de tarefas. Descreva em uma linha, citando as entidades principais.

## 8. Arquitetura atual

| Classificação | Sinais |
|---|---|
| Monolítica sem camadas | poucos arquivos; o mesmo arquivo tem SQL, regra de negócio e rota; uma classe que cria o banco e registra rotas |
| Camadas parciais | já existem pastas como `models/`, `routes/`, `services/`, mas as rotas consultam o banco, validam e calculam |
| MVC / camadas completas | rotas só recebem e respondem; controllers coordenam; SQL só nos models; config e tratamento de erro centralizados |

Descreva em uma linha o que existe hoje e onde estão as misturas principais.

## 9. Contagem de arquivos e linhas

Conte só código-fonte (respeitando a seção 1). Exemplo:

```bash
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" \
  -not -path "*/.claude/*" -not -path "*/__pycache__/*" | xargs wc -l
```

O número de "Source files" do resumo tem que bater com essa lista.

## 10. Saída da Fase 1

Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework> <versão>
Dependencies:  <dependências de runtime, separadas por vírgula>
Domain:        <domínio> (<entidades principais>)
Architecture:  <classificação> — <uma linha com a evidência>
Source files:  <N> files analyzed (~<linhas> lines)
DB tables:     <tabelas, separadas por vírgula>
Database:      <banco e forma de acesso>
Entry point:   <arquivo> (porta <porta>) — run: <comando>
Endpoints:     <N> routes
================================
```

Logo abaixo, liste as rotas do inventário (método, caminho, arquivo:linha).
