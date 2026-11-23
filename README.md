# Skill refactor-arch: auditoria e refatoração para MVC

A `refactor-arch` é uma skill para o Claude Code que audita projetos backend e os reorganiza no padrão MVC, e foi executada nos três projetos legados deste repositório. Ela começa analisando a stack e gerando um relatório de anti-patterns, pede confirmação antes de mexer em qualquer arquivo e, só depois da resposta, refatora o código e verifica se a API continua respondendo como antes.

## Análise Manual

Os problemas abaixo foram identificados pela leitura do código dos três projetos, antes da construção da skill, e serviram de base para o catálogo de anti-patterns. As linhas indicadas se referem à versão original de cada projeto.

### Projeto 1 — code-smells-project (Python/Flask, e-commerce)

| #  | Severidade | Problema | Arquivo:linha | Justificativa |
| -- | ---------- | -------- | ------------- | ------------- |
| 1  | CRITICAL | Execução de SQL sem controle e autenticação | `app.py:47-78` | Qualquer pessoa pode ler, alterar ou apagar o banco inteiro com um POST. |
| 2  | CRITICAL | Credenciais expostas | `app.py:7-8, 88`; `database.py:75-78` | Chave, senhas e modo debug ficam expostos no código. |
| 3  | CRITICAL | SQL Injection: queries montadas por concatenação | `models.py:24-29, 43-60, 89-111, 122-129, 275-300` | Permite entrar sem senha digitando `' OR '1'='1` no campo de e-mail do login. |
| 4  | HIGH | Acoplamento indevido de tarefas distintas em um único arquivo | `models.py:1-314` | Quatro domínios no mesmo arquivo impedem testar qualquer parte isolada. |
| 5  | HIGH | Acoplamento indevido de rotas e lógica administrativa na inicialização | `app.py:11-30, 32-78` | O arquivo de entrada mistura inicialização, rotas e SQL. |
| 6  | HIGH | Conexão SQLite global compartilhada entre requisições | `database.py:4-11` | Requisições simultâneas compartilham a mesma conexão e interferem entre si. |
| 7  | MEDIUM | Queries N+1 ao carregar pedidos e seus itens/produtos | `models.py:171-233` | Cada pedido e cada item geram uma consulta nova. |
| 8  | MEDIUM | Validação de dados insuficiente | `controllers.py:87-90, 169-171, 239-240` | Dados inválidos entram no banco e corpo vazio gera erro 500. |
| 9  | LOW | Regras de negócio direto no código | `models.py:247-262, 275-283` | Faixas de desconto e status ficam soltos no código. |
| 10 | LOW | Variáveis com nomes pouco expressivos | `models.py:24, 89, 187-191, 219-223` | `cursor2`, `cursor3` e `id` não dizem o que guardam. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

| # | Severidade | Problema | Arquivo:linha | Justificativa |
| - | ---------- | -------- | ------------- | ------------- |
| 1 | CRITICAL | Credenciais expostas | `src/utils.js:1-7` | Senha do banco e chave de pagamento ficam no repositório. |
| 2 | CRITICAL | Exposição indevida nos logs | `src/AppManager.js:43-46` | Cartão e chave do gateway vão para o log a cada compra. |
| 3 | CRITICAL | Concentração de escopo indevida em uma única classe | `src/AppManager.js:4-138` | Banco, rotas e checkout ficam presos na mesma classe. |
| 4 | HIGH | Checkout executa várias gravações sem transação atômica | `src/AppManager.js:43-63, 66-75` | Uma falha no meio deixa matrícula sem pagamento. |
| 5 | HIGH | Proteção criptográfica fraca | `src/utils.js:17-23`; uso em `src/AppManager.js:68-70` | O "hash" é reversível e a senha padrão é "123456". |
| 6 | MEDIUM | Consulta N+1 no relatório financeiro | `src/AppManager.js:80-129` | Uma consulta por curso e mais duas por aluno. |
| 7 | MEDIUM | Erros de banco são ignorados em partes do fluxo | `src/AppManager.js:57-61, 92-107, 131-136` | Falhas passam em silêncio ou derrubam o servidor. |
| 8 | LOW | Variável global exportada e nunca usada | `src/utils.js:10, 25`; `src/AppManager.js:2` | `totalRevenue` é exportada e ninguém usa. |
| 9 | LOW | Variáveis com nomes pouco expressivos | `src/AppManager.js:26-35, 89-106` | `u`, `e`, `p` e `cc` não dizem o que guardam. |

### Projeto 3 — task-manager-api (Python/Flask, gerenciador de tarefas)

| # | Severidade | Problema | Arquivo:linha | Justificativa |
| - | ---------- | -------- | ------------- | ------------- |
| 1 | CRITICAL | Credenciais expostas | `services/notification_service.py:7-10`; `app.py:11-13` | Senha do e-mail e `SECRET_KEY` ficam no repositório. |
| 2 | HIGH | Proteção criptográfica fraca | `models/user.py:27-32` | MD5 sem salt se quebra com tabelas prontas. |
| 3 | HIGH | Exposição indevida na resposta | `models/user.py:16-25` | `to_dict()` devolve o hash da senha nas respostas. |
| 4 | HIGH | Lógica de aplicação e consultas diretamente nas rotas | `routes/task_routes.py:10-299`; `routes/user_routes.py:10-211`; `routes/report_routes.py:12-223` | As rotas consultam o banco, validam e montam a resposta. |
| 5 | MEDIUM | Relatório de resumo executa consultas repetidas e N+1 | `routes/report_routes.py:15-68` | Mais de 15 consultas fixas e mais uma por usuário. |
| 6 | MEDIUM | Endpoint de estatísticas carrega todas sem filtro | `routes/task_routes.py:273-299` | Carrega todas as tasks só para contar as atrasadas. |
| 7 | MEDIUM | APIs deprecated: `Query.get()` e `datetime.utcnow()` | `Query.get()`: `routes/user_routes.py:29, 94, 136, 155`; `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/report_routes.py:105, 192, 213`. `utcnow()`: `models/user.py:14`; `models/category.py:11`; `models/task.py:15-16, 52`; `routes/task_routes.py:31, 72, 215, 285`; `routes/report_routes.py:35, 42, 45, 71, 133`; `routes/user_routes.py:172` | São APIs obsoletas que podem deixar de funcionar nas próximas versões do SQLAlchemy e do Python. |
| 8 | LOW | Imports sem uso e imports agrupados sem clareza | `app.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `utils/helpers.py:3-7` | Poluem o arquivo e escondem as dependências reais. |
| 9 | LOW | Valores de domínio repetidos como magic numbers | `routes/user_routes.py:64-65, 115-116`; `routes/task_routes.py:166-184`; `models/task.py:38-48` | Os mesmos limites se repetem em vários arquivos. |

## Construção da Skill

### Organização dos arquivos

```
.claude/skills/refactor-arch/
├── SKILL.md
└── references/
    ├── project-analysis.md       # Fase 1: detecção de stack, banco, rotas e arquitetura
    ├── anti-patterns.md          # Fase 2: catálogo com sinais de detecção e severidade
    ├── report-template.md        # Fase 2: formato do relatório, pausa e gravação
    ├── mvc-guidelines.md         # Fase 3: responsabilidades e proibições de cada camada
    └── refactoring-playbook.md   # Fase 3: transformações com código antes/depois
```

Cada área de conhecimento exigida tem o seu próprio arquivo de referência, o que deixa a cobertura fácil de conferir e faz o agente carregar apenas o que a fase atual precisa. O `SKILL.md` funciona como roteiro, definindo o que fazer e em que ordem, e cada fase começa com a instrução de ler as referências correspondentes, já que uma instrução que não aponta o arquivo não garante que ele seja consultado. Como a skill altera arquivos, o frontmatter usa `disable-model-invocation: true`, e por isso ela só roda quando alguém digita `/refactor-arch`.

### Fluxo das fases

1. Na análise, a skill detecta linguagem, framework, banco, domínio e rotas a partir de evidências, como o arquivo de dependências, os imports e o entry point, e imprime um resumo sem alterar nada.
2. Na auditoria, o código é cruzado com o catálogo e o relatório sai ordenado de CRITICAL a LOW, com arquivo e linha em cada achado. A resposta termina com `Proceed with refactoring (Phase 3)? [y/n]`, e nenhum arquivo é tocado até o usuário responder. Depois do "y", o relatório é gravado em `reports/`, reaproveitando o arquivo do mesmo projeto quando ele já existe.
3. Na refatoração, a aplicação original sobe primeiro para que as respostas de todas as rotas fiquem gravadas numa pasta temporária fora do projeto. Só então o código é reorganizado, a aplicação sobe de novo com o mesmo comando e as respostas são comparadas por status e campos. Quando algo quebra, a skill corrige e repete a validação, até cinco vezes, e ao final lista as mudanças de resposta feitas por segurança e o que ainda sobrou do catálogo.

### Decisões de design

| Ponto em aberto | Decisão |
|---|---|
| Local do código refatorado | Camadas em `src/` (`config/`, `models/`, `views/`, `controllers/`, `middlewares/`), preservando o comando original de execução. Em projetos que já têm pastas equivalentes, a estrutura existente é mantida e a equivalência fica registrada. |
| View numa API JSON | Camada HTTP, responsável pela rota, pela leitura da requisição e pelo formato da resposta. |
| Pasta `services/` | Reservada a integrações externas, como e-mail e gateway, enquanto o fluxo fica nos controllers e as regras de entidade nos models. |
| Critério de "endpoint continua respondendo" | Mesma rota, mesmo método, mesmo status e mesmos campos, com exceção apenas para correções de segurança, como deixar de devolver a senha, que precisam aparecer no resumo final. |

### Catálogo de anti-patterns

O catálogo tem 19 anti-patterns. Cada problema da análise manual virou um anti-pattern com sinais de detecção concretos, e a lista foi completada com padrões que costumam aparecer em backends desse tipo.

| Severidade | Anti-patterns | Motivo da inclusão |
|---|---|---|
| CRITICAL | AP-01 credenciais hardcoded, AP-02 SQL Injection, AP-03 endpoint sensível sem autenticação, AP-04 God Class, AP-05 dado sensível em resposta ou log | Aparecem nos três projetos e expõem dados ou o banco inteiro, e a God Class é o próprio exemplo de CRITICAL da escala do desafio. |
| HIGH | AP-06 senha sem hash forte, AP-07 regra de negócio na rota, AP-08 estado global mutável, AP-09 gravações sem transação | São as violações de MVC e SOLID que mais travam a separação em camadas, e a da transação veio do checkout do projeto 2. |
| MEDIUM | AP-10 N+1, AP-11 validação ausente, AP-12 erro genérico ou ignorado, AP-13 agregação em memória, AP-14 duplicação, AP-15 API deprecated | Cobrem performance e padronização, e o item de deprecated traz uma tabela com o substituto de cada API em Python e em Node. |
| LOW | AP-16 magic numbers, AP-17 nomes ruins, AP-18 `print` no lugar de log, AP-19 imports sem uso e código morto | Afetam a legibilidade e aparecem em praticamente todo projeto legado, embora sejam fáceis de corrigir. |

Cada anti-pattern aponta para uma das 13 transformações do playbook (T01 a T13), e todas elas têm exemplo antes/depois em Python e em JavaScript.

### Agnosticismo de tecnologia

O `SKILL.md` não cita nenhum arquivo, rota ou comando de projeto, porque tudo isso é descoberto a cada execução. A detecção da Fase 1 tem tabelas por linguagem e framework (Flask, FastAPI, Django, Express, Fastify e NestJS) e lê a versão no arquivo de dependências e no lockfile, enquanto os sinais de cada anti-pattern vêm escritos em Python e em JavaScript. As guidelines trazem a estrutura alvo para as duas stacks e uma seção específica para projetos que já têm alguma organização, orientando a mapear as pastas existentes para camadas em vez de reescrever tudo. A pasta da skill foi copiada sem nenhuma alteração para os outros dois projetos, e as três cópias são idênticas.

### Desafios encontrados

Exigir token nas rotas administrativas muda o status delas de 200 para 401, o que entraria em conflito com a ideia de manter os endpoints respondendo. A saída foi definir o critério de "continua respondendo" com uma exceção explícita para correções de segurança, que a skill precisa listar no resumo final.

No Flask-SQLAlchemy, o SQLite com caminho relativo é criado em `instance/`, ao lado do módulo da aplicação, então mover a aplicação de pasta mudaria o arquivo do banco sem nenhum aviso. Por isso as guidelines exigem um caminho fixo e uma nova execução do seed para conferir que os dados continuam no mesmo lugar.

Duas armadilhas de tratamento de erro precisaram entrar no playbook. O Express 4 não captura erros de funções `async`, por isso o exemplo inclui um `asyncHandler` junto com o middleware de erro, e no Flask um `errorhandler(Exception)` transformaria o 404 de rota inexistente em 500, então o exemplo deixa passar as exceções HTTP.

Na primeira rodada, o Claude Code entrou em auto mode e a resposta parou logo depois do primeiro comando, mas um "continue" foi suficiente para retomar a execução ainda na Fase 1.

No projeto 3, o relatório marcou `POST /users` como endpoint sem autenticação, já que qualquer pessoa conseguia se cadastrar como admin, só que bloquear o cadastro inteiro quebraria uma rota pública. Na pausa da Fase 2, a resposta foi "y" acompanhada de uma orientação para manter o cadastro aberto e exigir token apenas para criar admin ou mudar `role` e `active`. A skill seguiu a orientação e, no resumo final, apontou o risco que sobrou em vez de declarar que não restavam anti-patterns.

Para não depender só do que a skill declarava, um baseline de cada projeto foi gravado com scripts de `curl` próprios antes da execução, e os mesmos scripts rodaram de novo depois de cada refatoração.

## Resultados

### Findings por projeto

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Itens da análise manual encontrados |
|---|---|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 | 4 | 5 | 5 | 4 | 18 | 10 de 10 |
| ecommerce-api-legacy | Node.js + Express 4.22.1 | 4 | 4 | 5 | 4 | 17 | 9 de 9 |
| task-manager-api | Python + Flask 3.0.0 | 3 | 3 | 6 | 4 | 16 | 9 de 9 |

Os relatórios completos estão em [`reports/`](reports/).

### Estrutura antes e depois

**Projeto 1 — code-smells-project**

```
Antes                         Depois
app.py                        app.py                  # entry point: python app.py
controllers.py                .env.example
database.py                   src/
models.py                     ├── app.py              # create_app()
requirements.txt              ├── config/settings.py
                              ├── models/             # database, seed, produto, usuario, pedido, admin
                              ├── views/              # Blueprints: produto, usuario, pedido, admin
                              ├── controllers/        # produto, usuario, pedido, relatorio, admin
                              ├── services/notification_service.py
                              └── middlewares/        # errors, error_handler, auth
```

**Projeto 2 — ecommerce-api-legacy**

```
Antes                         Depois
src/app.js                    src/app.js              # composition root, npm start
src/AppManager.js             .env.example
src/utils.js                  src/config/             # settings, logger
                              src/models/             # database, user, course, enrollment, payment, auditLog, report
                              src/views/              # Routers: checkout, report, user
                              src/controllers/        # checkout, report, user
                              src/services/paymentService.js
                              src/middlewares/        # errors, errorHandler, asyncHandler, requireAdmin
                              src/utils/password.js   # scrypt com salt
```

**Projeto 3 — task-manager-api**

```
Antes                         Depois
app.py                        app.py                  # create_app(), python app.py
database.py                   .env.example
seed.py                       seed.py                 # sem alteração
models/                       config/                 # settings, constants
routes/                       models/                 # database, task, user, category
services/                     routes/                 # task, user, report, category, health
utils/                        controllers/            # task, user, category, report, validators
                              middlewares/            # errors, error_handler, auth
```

No projeto 3 a skill não criou a pasta `src/`: manteve `models/` e `routes/`, com `routes/` fazendo o papel das views, criou as camadas que faltavam e removeu `services/` e `utils/`, porque nenhuma rota usava essas pastas e o service ainda guardava a senha SMTP no código.

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** | | | |
| Linguagem detectada corretamente | Sim (Python) | Sim (JavaScript) | Sim (Python) |
| Framework detectado corretamente | Sim (Flask 3.1.1) | Sim (Express 4.22.1) | Sim (Flask 3.0.0) |
| Domínio descrito corretamente | Sim (e-commerce) | Sim (LMS com checkout) | Sim (gerenciador de tarefas) |
| Número de arquivos condiz com a realidade | Sim (4) | Sim (3) | Sim (15) |
| **Fase 2** | | | |
| Relatório segue o template | Sim | Sim | Sim |
| Cada finding tem arquivo e linhas exatos | Sim | Sim | Sim |
| Findings ordenados de CRITICAL a LOW | Sim | Sim | Sim |
| Mínimo de 5 findings | Sim (18) | Sim (17) | Sim (16) |
| Detecção de APIs deprecated | Sim (nenhuma no projeto) | Sim (nenhuma no projeto) | Sim (`Query.get()`) |
| Pausa e pede confirmação antes da Fase 3 | Sim | Sim | Sim |
| **Fase 3** | | | |
| Estrutura de diretórios segue MVC | Sim | Sim | Sim (`routes/` no papel de views) |
| Configuração extraída, sem hardcoded | Sim | Sim | Sim |
| Models abstraem os dados | Sim | Sim | Sim |
| Views/Routes separadas | Sim | Sim | Sim |
| Controllers concentram o fluxo | Sim | Sim | Sim |
| Error handling centralizado | Sim | Sim | Sim |
| Entry point claro | Sim (`python app.py`) | Sim (`npm start`) | Sim (`python app.py`) |
| Aplicação inicia sem erros | Sim | Sim | Sim |
| Endpoints originais respondem | Sim (21/23; as 2 rotas `/admin` passaram a exigir token) | Sim (4/4 do checkout; relatório e delete passaram a exigir token) | Sim (25/25) |

### Logs das aplicações após a refatoração

Os scripts de `curl` do baseline rodaram de novo com o banco recriado e o mesmo comando de execução de antes, e nos três casos o servidor subiu sem nenhum traceback.

**Projeto 1** (`python app.py`)

```
WARNING src.app: SECRET_KEY não definida; usando chave aleatória temporária.
WARNING src.app: ADMIN_TOKEN não definido; rotas /admin/* ficam bloqueadas.
INFO src.models.seed: Banco populado com dados de exemplo
INFO __main__: Servidor iniciado em http://localhost:5000
 * Debug mode: off

GET /                    antes 200 | depois 200     POST /usuarios           antes 201 | depois 201
GET /health              antes 200 | depois 200     POST /login              antes 200 | depois 200
GET /produtos            antes 200 | depois 200     POST /login (errado)     antes 401 | depois 401
GET /produtos/busca?q=a  antes 200 | depois 200     POST /pedidos            antes 201 | depois 201
GET /produtos/1          antes 200 | depois 200     GET /pedidos             antes 200 | depois 200
GET /produtos/9999       antes 404 | depois 404     GET /pedidos/usuario/2   antes 200 | depois 200
POST /produtos (3 casos) antes 400 201 400 | igual  PUT /pedidos/1/status    antes 200 | depois 200
PUT /produtos/1          antes 200 | depois 200     GET /relatorios/vendas   antes 200 | depois 200
GET /usuarios            antes 200 | depois 200     DELETE /produtos/3       antes 200 | depois 200
GET /usuarios/1          antes 200 | depois 200     POST /admin/query        antes 200 | depois 401 (sem token)
                                                    POST /admin/reset-db     antes 200 | depois 401 (sem token)
```

Quando a requisição traz o header `X-Admin-Token`, `/admin/query` responde 200 para SELECT e 400 para qualquer outro comando, e `/admin/reset-db` responde 200. As respostas também ficaram mais enxutas por segurança, já que `/usuarios` deixou de devolver o campo `senha` e `/health` deixou de expor `secret_key`, `debug` e `db_path`.

**Projeto 2** (`npm start`)

```
[WARN] ADMIN_TOKEN não definido; rotas administrativas ficam bloqueadas.
[INFO] LMS API rodando na porta 3000...
[INFO] Processando cartão final 4444 no valor de 497

POST /api/checkout (sucesso)           antes 200 | depois 200
POST /api/checkout (cartão recusado)   antes 400 | depois 400
POST /api/checkout (curso inexistente) antes 404 | depois 404
POST /api/checkout (corpo incompleto)  antes 400 | depois 400
GET  /api/admin/financial-report       antes 200 | depois 401 (sem token) | 200 (com token)
DELETE /api/users/1                    antes 200 | depois 401 (sem token) | 200 (com token)
```

O log, que antes imprimia o número inteiro do cartão e a chave do gateway, agora mostra só os quatro últimos dígitos do cartão.

**Projeto 3** (`python seed.py` e `python app.py`)

```
WARNING __main__: SECRET_KEY não definida; usando chave aleatória (tokens expiram a cada reinício).
 * Debug mode: off

GET /, /health, /tasks, /tasks/1, /tasks/search, /tasks/stats   200 | 200
GET /tasks/9999                                                 404 | 404
POST /tasks (válida | título curto)                             201 400 | 201 400
PUT /tasks/1, DELETE /tasks/2                                   200 | 200
GET /users, /users/1, /users/1/tasks, PUT /users/1              200 | 200
POST /users                                                     201 | 201
DELETE /users/3                                                 200 | 200
POST /login (certo | errado)                                    200 401 | 200 401
GET /reports/summary, /reports/user/1, /categories              200 | 200
POST /categories                                                201 | 201
PUT /categories/1, DELETE /categories/4                         200 | 200
```

As 25 requisições voltaram com o mesmo status e os mesmos campos, com exceção de `password`, que saiu das respostas de usuário. O login com as senhas originais do seed continua funcionando e o banco permanece em `instance/tasks.db`.

### Comportamento da skill em cada stack

No projeto 1, um Flask monolítico, a refatoração foi a mais direta: os quatro arquivos foram separados em camadas dentro de `src/`, todo o SQL concatenado passou a usar placeholders e as senhas passaram a ser guardadas com hash. Na primeira validação outro processo respondeu na porta no lugar da aplicação nova, mas a skill percebeu que as respostas não batiam, refez o ciclo e passou na segunda tentativa.

No projeto 2, em Express, os callbacks aninhados viraram funções com `async/await` e o checkout passou a rodar dentro de uma transação. Alguns comportamentos mudaram sem alterar o formato da resposta, já que o relatório agora sai sempre na mesma ordem, o checkout recusado não cria mais o usuário e o DELETE apaga também as matrículas e os pagamentos do usuário. Por causa dessa última mudança, depois de um DELETE o relatório deixa de mostrar o aluno "Unknown" e a receita dele, e a mensagem de resposta do DELETE continua igual à original para não quebrar o contrato, mesmo dizendo que os dados "ficaram sujos".

No projeto 3, que já tinha camadas parciais, nada foi reescrito do zero: a lógica das rotas foi para controllers, as contagens viraram consultas agregadas e `Query.get()` deu lugar a `db.session.get()`. O `datetime.utcnow()` não foi marcado como deprecated porque o ambiente usa Python 3.10 e a depreciação só existe a partir do 3.12, enquanto a análise manual o incluiu pensando na próxima versão da linguagem. O resumo final também registrou o risco que sobrou da orientação dada na pausa, porque, com `PUT /users/<id>` ainda sem token, continua sendo possível trocar o e-mail ou a senha de outro usuário.

Quanto ao idioma, a narração do agente variou entre as execuções, em inglês no projeto 1 e em português nos projetos 2 e 3, enquanto os cabeçalhos do relatório seguiram o template, que usa o mesmo formato em inglês do exemplo do desafio.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (testado na versão 2.1.330)
- Python 3.10 ou superior, para os projetos 1 e 3
- Node.js e npm, para o projeto 2

### Execução da skill

A skill já está em `.claude/skills/refactor-arch/` dentro de cada projeto, e para executá-la de novo a partir do código original basta voltar o projeto ao commit inicial (`6d1ce62`) mantendo a pasta `.claude/`.

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Depois de imprimir o resumo da Fase 1 e o relatório da Fase 2, a skill para em `Proceed with refactoring (Phase 3)? [y/n]`. Com "y", o relatório é gravado em `reports/audit-project-N.md` e a refatoração começa, e com "n" a execução termina sem alterar nenhum arquivo.

### Validação da refatoração

**Projeto 1**

```bash
cd code-smells-project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
ADMIN_TOKEN=um-token-qualquer .venv/bin/python app.py
```

```bash
curl -i http://localhost:5000/produtos                      # 200
curl -i http://localhost:5000/usuarios                      # 200, sem o campo senha
curl -i -X POST http://localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","senha":"123456"}'          # 200
curl -i -X POST http://localhost:5000/admin/reset-db        # 401
curl -i -X POST http://localhost:5000/admin/reset-db -H 'X-Admin-Token: um-token-qualquer'   # 200
```

**Projeto 2**

```bash
cd ecommerce-api-legacy
npm install
ADMIN_TOKEN=um-token-qualquer npm start
```

As requisições de `api.http` continuam válidas, mas as duas rotas administrativas, que antes eram abertas, agora só respondem com o header `X-Admin-Token`:

```bash
curl -i -X POST http://localhost:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'   # 200
curl -i http://localhost:3000/api/admin/financial-report -H 'X-Admin-Token: um-token-qualquer'                  # 200
```

**Projeto 3**

```bash
cd task-manager-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
.venv/bin/python app.py
```

```bash
curl -i http://localhost:5000/tasks                         # 200
curl -i http://localhost:5000/users/1                       # 200, sem o campo password
curl -i -X POST http://localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"maria@email.com","password":"abcd"}'        # 200, devolve o token
```

Antes da refatoração, qualquer pessoa podia criar um usuário admin ou alterar `role` e `active` de outro usuário. Agora essas duas operações exigem o header `Authorization: Bearer <token>`, preenchido com o token que o `/login` devolve para um usuário admin, enquanto o cadastro comum continua aberto.

Cada projeto tem um `.env.example` com as variáveis que a aplicação lê, e, quando `SECRET_KEY` não está definida, a aplicação gera uma chave aleatória a cada boot e registra um aviso no log.
