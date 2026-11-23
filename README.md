# Skill refactor-arch: auditoria e refatoração para MVC

A `refactor-arch` é uma skill do Claude Code que analisa um projeto backend, aponta os problemas de arquitetura e reorganiza o código no padrão MVC. Ela foi usada nos três projetos legados deste repositório. Primeiro a skill descobre a stack e gera um relatório com os problemas encontrados, depois pede confirmação e só então altera o código, conferindo no fim se a API continua respondendo como antes.

## Análise Manual

Os problemas abaixo foram encontrados lendo o código dos três projetos, antes de a skill existir, e serviram de base para o catálogo de anti-patterns. As linhas se referem à versão original de cada projeto.

### Projeto 1 — code-smells-project (Python/Flask, e-commerce)

| #  | Severidade | Problema | Arquivo:linha | Justificativa |
| -- | ---------- | -------- | ------------- | ------------- |
| 1  | CRITICAL | Execução de SQL sem controle e autenticação | `app.py:47-78` | Qualquer pessoa pode ler, alterar ou apagar o banco inteiro com um POST. |
| 2  | CRITICAL | Credenciais expostas | `app.py:7-8, 88`; `database.py:75-78` | Chave, senhas e modo debug ficam expostos no código. |
| 3  | CRITICAL | SQL Injection: queries montadas por concatenação | `models.py:24-29, 43-60, 89-111, 122-129, 275-300` | Permite entrar sem senha digitando `' OR '1'='1` no campo de e-mail do login. |
| 4  | HIGH | Acoplamento indevido de tarefas distintas em um único arquivo | `models.py:1-314` | Quatro domínios no mesmo arquivo impedem testar qualquer parte isolada. |
| 5  | HIGH | Acoplamento indevido de rotas e lógica administrativa na inicialização | `app.py:11-30, 32-78` | O arquivo de entrada mistura inicialização, rotas e SQL. |
| 6  | HIGH | Conexão SQLite global compartilhada entre requisições | `database.py:4-11` | Requisições simultâneas usam a mesma conexão e atrapalham umas às outras. |
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
| 7 | MEDIUM | APIs deprecated: `Query.get()` e `datetime.utcnow()` | `Query.get()`: `routes/user_routes.py:29, 94, 136, 155`; `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/report_routes.py:105, 192, 213`. `utcnow()`: `models/user.py:14`; `models/category.py:11`; `models/task.py:15-16, 52`; `routes/task_routes.py:31, 72, 215, 285`; `routes/report_routes.py:35, 42, 45, 71, 133`; `routes/user_routes.py:172` | São APIs antigas que podem deixar de funcionar nas próximas versões do SQLAlchemy e do Python. |
| 8 | LOW | Imports sem uso e imports agrupados sem clareza | `app.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `utils/helpers.py:3-7` | Poluem o arquivo e escondem do que o código depende de verdade. |
| 9 | LOW | Valores de domínio repetidos como magic numbers | `routes/user_routes.py:64-65, 115-116`; `routes/task_routes.py:166-184`; `models/task.py:38-48` | Os mesmos limites se repetem em vários arquivos. |

## Construção da Skill

### Organização dos arquivos

```
.claude/skills/refactor-arch/
├── SKILL.md
├── references/
│   ├── project-analysis.md              # Fase 1: como descobrir stack, banco, rotas e arquitetura
│   ├── anti-patterns.md                 # Fase 2: catálogo com sinais de detecção e severidade
│   ├── report-template.md               # Fase 2: formato do relatório, pausa e gravação
│   ├── mvc-guidelines.md                # Fase 3: o que cada camada faz e o que não pode fazer
│   └── refactoring-playbook.md          # Fase 3: como corrigir cada problema, com código antes e depois
└── scripts/
    ├── wait_for_http.sh                 # espera a aplicação responder
    ├── run_requests.sh                  # faz as requisições e mostra o status e os campos de cada resposta
    ├── compare_results.sh               # compara o antes e o depois, linha a linha
    └── stop_port.sh                     # para a aplicação pela porta e confere se ela ficou livre
```

Cada assunto pedido tem um arquivo de referência próprio, assim fica fácil conferir se nada faltou e o agente lê só o que a fase atual precisa. O `SKILL.md` é o roteiro, diz o que fazer e em que ordem, e cada fase começa mandando ler o arquivo de referência certo, porque uma instrução que não aponta o arquivo não garante que ele seja lido. Ele também tem uma tabela que diz qual arquivo ler em cada fase e cita as seções pelo título, e não por número. A comparação das respostas da API é feita por scripts, e não descrita em texto, porque um script mostra o resultado sempre do mesmo jeito. Como a skill altera arquivos, ela só roda quando alguém digita `/refactor-arch`, o que é garantido pela opção `disable-model-invocation: true` no cabeçalho do `SKILL.md`.

### Fluxo das fases

1. Na análise, a skill descobre a linguagem, o framework, o banco, o domínio e as rotas olhando o arquivo de dependências, os imports e o arquivo de entrada, e mostra um resumo sem alterar nada.
2. Na auditoria, a skill compara o código com o catálogo e monta um relatório do mais grave (CRITICAL) para o menos grave (LOW), com arquivo e linha em cada problema. Antes de mostrar o relatório, ela confere de novo cada problema que encontrou. A resposta termina com a pergunta `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, e nada é alterado até o usuário responder. Com "y", o relatório é gravado em `reports/`, no mesmo arquivo usado da última vez para aquele projeto.
3. Na refatoração, a skill primeiro sobe a aplicação original e guarda as respostas de todas as rotas numa pasta temporária, fora do projeto. Depois reorganiza o código, sobe a aplicação de novo com o mesmo comando e usa os scripts para comparar o status e os campos de cada resposta com os de antes. Se algo quebrar, ela corrige e testa de novo, no máximo cinco vezes. No fim, lista as respostas que mudaram por segurança e os problemas do catálogo que ainda ficaram.

### Decisões de design

| Ponto em aberto | Decisão |
|---|---|
| Onde fica o código refatorado | Nas pastas `config/`, `models/`, `views/`, `controllers/` e `middlewares/`, dentro de `src/`, sem mudar o comando que roda a aplicação. Se o projeto já tem pastas com o mesmo papel, elas são mantidas e o resumo final diz qual pasta faz o papel de qual camada. |
| O que é a View numa API JSON | A camada que recebe a requisição HTTP, lê os dados e monta a resposta. Não há telas. |
| Para que serve a pasta `services/` | Só para falar com sistemas de fora, como e-mail e gateway de pagamento. O fluxo de cada operação fica nos controllers, e as regras de cada entidade ficam nos models. |
| Quando um endpoint "continua respondendo" | Quando mantém a mesma rota, o mesmo método, o mesmo status e os mesmos campos. A única mudança permitida é a de segurança, como deixar de devolver a senha, e ela precisa aparecer no resumo final. |

### Catálogo de anti-patterns

O catálogo tem 19 anti-patterns. Cada problema da análise manual virou um anti-pattern com sinais concretos para encontrá-lo no código, e a lista foi completada com problemas comuns nesse tipo de backend.

| Severidade | Anti-patterns | Por que entrou |
|---|---|---|
| CRITICAL | AP-01 credenciais no código, AP-02 SQL Injection, AP-03 rota sensível sem autenticação, AP-04 God Class, AP-05 dado sensível em resposta ou log | Aparecem nos três projetos e expõem dados ou o banco inteiro. A God Class é o próprio exemplo de CRITICAL usado no desafio. |
| HIGH | AP-06 senha sem hash forte, AP-07 regra de negócio na rota, AP-08 estado global que muda, AP-09 gravações sem transação | São os problemas que mais atrapalham separar o código em camadas. O da transação veio do checkout do projeto 2. |
| MEDIUM | AP-10 N+1, AP-11 falta de validação, AP-12 erro genérico ou ignorado, AP-13 conta feita no código em vez de no banco, AP-14 código duplicado, AP-15 API deprecated | Tratam de desempenho e de padronização. O item de API deprecated traz uma tabela com o substituto de cada uma em Python e em Node. |
| LOW | AP-16 magic numbers, AP-17 nomes ruins, AP-18 `print` no lugar de log, AP-19 imports sem uso e código morto | Deixam o código difícil de ler e aparecem em quase todo projeto antigo, mas são fáceis de corrigir. |

Cada anti-pattern indica qual das 13 correções do playbook resolve o problema (T01 a T13), e todas têm exemplo de antes e depois em Python e em JavaScript. Antes de fechar o relatório, a skill revê os próprios achados: tira os que estavam errados e marca como `(possible)` os que ela não conseguiu provar só pelo código.

### Agnosticismo de tecnologia

O `SKILL.md` não cita nenhum arquivo, rota ou comando de um projeto específico, porque a skill descobre tudo isso a cada execução. A análise da Fase 1 tem tabelas para vários frameworks (Flask, FastAPI, Django, Express, Fastify e NestJS) e lê a versão no arquivo de dependências, e os sinais de cada anti-pattern estão escritos em Python e em JavaScript. As guidelines mostram a estrutura final para as duas linguagens e têm uma seção para projetos que já estão parcialmente organizados, que manda aproveitar as pastas existentes em vez de reescrever tudo. As correções são as mesmas em qualquer linguagem, e o playbook mostra cada uma em Python e em JavaScript para servir de modelo. A pasta da skill foi copiada sem nenhuma mudança para os outros dois projetos, e as três cópias são iguais.

### Desafios encontrados

Exigir token nas rotas de administrador muda a resposta delas de 200 para 401, o que vai contra a ideia de manter a API respondendo igual. Por isso a regra abriu uma exceção para as correções de segurança, que a skill precisa listar no resumo final.

No projeto 2, a skill não seguiu essa regra. Ela também mudou respostas que não tinham a ver com segurança, como a mensagem do DELETE e o erro 404 para um usuário que não existe. A skill avisou dessas mudanças no resumo e ofereceu desfazer tudo, mas elas foram mantidas, porque a mensagem antiga dizia que os dados do usuário apagado "ficaram sujos no banco", e depois da correção isso deixou de acontecer. A regra da skill continua a mesma, ou seja, manter essas mudanças foi uma decisão manual, e não algo que a skill permite.

No Flask-SQLAlchemy, um banco SQLite com caminho relativo é criado na pasta `instance/`, ao lado do código da aplicação. Se a aplicação muda de pasta, o banco vai junto sem nenhum aviso. Por isso as guidelines mandam fixar o caminho do banco e rodar o seed de novo para conferir que os dados continuam no mesmo lugar.

Dois cuidados com tratamento de erro entraram no playbook. O Express 4 não captura erros de funções `async`, então o exemplo traz um `asyncHandler` junto com o middleware de erro. No Flask, um `errorhandler(Exception)` transformaria o 404 de uma rota que não existe em erro 500, então o exemplo deixa os erros HTTP passarem.

Na primeira rodada, o Claude Code entrou em auto mode e parou logo depois do primeiro comando, e bastou digitar "continue" para seguir. Na segunda, a execução parou depois do "y" esperando uma permissão, porque a pasta `reports/` fica na raiz do repositório, fora da pasta do projeto, e o Claude Code pergunta antes de ler ou gravar arquivos fora dela.

No projeto 3, o relatório apontou o `POST /users` como rota sem autenticação, já que qualquer pessoa podia se cadastrar como admin, mas bloquear a rota inteira impediria o cadastro comum. Por isso o "y" da pausa veio junto com uma orientação: manter o cadastro aberto e exigir token só para criar admin e para mudar `role` ou `active`. Na segunda rodada, a orientação passou a incluir também o `DELETE /users/<id>`, que apaga a conta e todas as tarefas dela. Nas duas vezes, a skill fez o que foi pedido.

Para não depender só do que a skill dizia, antes de rodar a skill foi feito um teste próprio de cada projeto, com scripts de `curl` fora do repositório, e os mesmos scripts rodaram de novo depois de cada refatoração. Esse teste é chamado de baseline no resto do texto.

### Refinamentos da skill

Depois da primeira rodada nos três projetos, a skill foi revista com base nas boas práticas de construção de skills e nos erros que apareceram durante as execuções.

| Problema | Decisão | Motivo |
|---|---|---|
| O `SKILL.md` citava seções por número, como "seção 10", mas só dois dos cinco arquivos de referência tinham títulos numerados | As citações passaram a usar o nome do arquivo e o título da seção, e o `SKILL.md` ganhou uma tabela que diz qual arquivo ler em cada fase | O título continua certo mesmo quando entra uma seção nova, e a tabela deixa claro o que ler em cada fase |
| Os arquivos de referência mais longos não tinham índice | Os que têm mais de 100 linhas ganharam uma linha "Seções" no topo | O agente acha a parte que precisa sem ler o arquivo inteiro |
| A comparação das respostas era descrita em texto, e cada execução montava os `curl` de um jeito | A comparação passou a ser feita pelos scripts `wait_for_http.sh`, `run_requests.sh` e `compare_results.sh` | Um script mostra o resultado sempre do mesmo jeito, o que permite comparar o antes e o depois |
| No projeto 1, a saída do campo `senha` não apareceu como diferença, porque ele fica dentro de `dados` e o script só olhava o primeiro nível da resposta | O `run_requests.sh` passou a olhar também os campos de dentro dos objetos e das listas | Sem isso, uma mudança de segurança passaria despercebida em APIs que colocam a resposta dentro de outro objeto |
| Nas duas rodadas do projeto 1, outro processo respondeu na porta no lugar da aplicação nova. Na segunda, ficou claro que o `pkill` pelo nome do comando não encontrou o processo | Foi criado o `stop_port.sh`, que para o processo pela porta e confere se ela ficou livre antes de subir outra versão | Se a porta não fica livre, a skill testa a aplicação antiga achando que é a nova |
| A skill rodou `git rm --cached` nos projetos 2 e 1, em rodadas diferentes, porque a regra só proibia commit e push | A regra passou a listar todos os comandos git que alteram o repositório e manda usar `rm` e `mv` do sistema | Quem cuida do git é o usuário, e uma regra que lista os comandos não deixa brecha |
| O relatório não tinha como marcar um problema que não dava para provar só pelo código | Antes de fechar o relatório, a skill revê cada problema, tira os errados e marca como `(possible)` os que dependem de algo fora do código | Quem lê o relatório sabe o que foi provado e o que ainda precisa ser confirmado |
| Com Python e JavaScript no mesmo playbook, o agente lê os exemplos das duas linguagens mesmo quando o projeto usa só uma | O playbook chegou a ser dividido em um arquivo por linguagem, e a divisão foi desfeita | As correções são as mesmas em qualquer linguagem, e um arquivo só deixa claro que a skill não depende de uma stack |

Ficou um limite no script de comparação: quando a resposta é um texto, e não um JSON, o `run_requests.sh` registra só a palavra `text`. Por isso a mudança na mensagem do DELETE do projeto 2 não apareceu como diferença no script, só no resumo da skill e no baseline.

Depois desses ajustes, os três projetos voltaram ao código original e foram refatorados de novo.

## Resultados

Os resultados abaixo são da segunda rodada, feita com a skill já ajustada, a partir do código original de cada projeto.

### Findings por projeto

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Itens da análise manual encontrados |
|---|---|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 | 5 | 4 | 5 | 4 | 18 | 10 de 10 |
| ecommerce-api-legacy | Node.js + Express 4.22.1 | 4 | 4 | 5 | 4 | 17 | 9 de 9 |
| task-manager-api | Python + Flask 3.0.0 | 3 | 3 | 6 | 4 | 16 | 9 de 9 |

Os relatórios completos estão em [`reports/`](reports/).

### Estrutura antes e depois

**Projeto 1 — code-smells-project**

```
Antes                         Depois
app.py                        app.py                  # entrada: python app.py
controllers.py                .env.example
database.py                   src/
models.py                     ├── app.py              # create_app()
requirements.txt              ├── config/settings.py
                              ├── models/             # database, seed, produto, usuario, pedido, admin
                              ├── views/              # Blueprints: produto, usuario, pedido, relatorio, sistema, admin
                              ├── controllers/        # produto, usuario, pedido, relatorio, sistema, admin
                              ├── services/notification_service.py
                              └── middlewares/        # errors, error_handler, auth
```

**Projeto 2 — ecommerce-api-legacy**

```
Antes                         Depois
src/app.js                    src/app.js              # liga todas as partes e sobe o servidor, npm start
src/AppManager.js             .env.example
src/utils.js                  src/config/             # settings, logger
                              src/models/             # database, user, course, enrollment, payment, auditLog, report
                              src/views/              # Routers: checkout, report, user
                              src/controllers/        # checkout, report, user
                              src/services/paymentService.js
                              src/middlewares/        # errors, errorHandler, asyncHandler, requireAdmin
                              src/utils/password.js   # hash scrypt com salt
```

**Projeto 3 — task-manager-api**

```
Antes                         Depois
app.py                        app.py                  # create_app(), python app.py
database.py                   .env.example
seed.py                       seed.py                 # grava as senhas com hash
models/                       config/                 # settings, constants
routes/                       models/                 # database, task, user, category
services/                     routes/                 # task, user, report, category, health
utils/                        controllers/            # task, user, category, report, validators
                              middlewares/            # errors, error_handler, auth
                              services/notification_service.py
                              utils/helpers.py
```

No projeto 3, a skill não criou a pasta `src/`, porque `models/` e `routes/` já existiam. A pasta `routes/` passou a fazer o papel das views, as camadas que faltavam foram criadas e as categorias saíram do arquivo de relatórios para um arquivo próprio. A pasta `services/` ficou, agora lendo os dados do SMTP da configuração, e a `utils/` ficou só com a única função usada.

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
| Detecção de APIs deprecated | Sim (nenhuma no projeto) | Sim (nenhuma no projeto) | Sim (`Query.get()` em 16 pontos) |
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
| Endpoints originais respondem | Sim (21 de 23 com o mesmo status; as 2 rotas `/admin` passaram a exigir token) | Sim (4 de 4 no checkout; relatório e DELETE passaram a exigir token) | Sim (24 de 25 com o mesmo status; o `DELETE /users` passou a exigir token) |

Os números da última linha vêm do baseline. A própria skill testou mais requisições e chegou a 41 de 45 no projeto 1, 6 de 10 no projeto 2 e 37 de 45 no projeto 3, e todas as respostas diferentes estavam na lista de mudanças do resumo final.

### Logs das aplicações após a refatoração

Os scripts do baseline rodaram de novo com o banco recriado e com o mesmo comando de antes, e nos três projetos a aplicação subiu sem nenhum erro.

**Projeto 1** (`python app.py`)

```
WARNING src.config.settings: SECRET_KEY não definida; usando chave aleatória temporária.
WARNING src.config.settings: ADMIN_TOKEN não definido; rotas /admin ficam bloqueadas.
INFO src.models.seed: Seed aplicado: 10 produtos, 3 usuários
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

Com o header `X-Admin-Token`, o `/admin/query` só aceita consultas SELECT, sem poder alterar o banco, e responde 400 para qualquer outro comando, enquanto o `/admin/reset-db` responde 200. O script de comparação também mostrou as respostas que perderam campos por segurança: o `/usuarios` não devolve mais a `senha`, que vinha dentro de `dados`, e o `/health` não mostra mais `secret_key`, `debug` e `db_path`.

**Projeto 2** (`npm start`)

```
WARN PAYMENT_GATEWAY_KEY não definida; gateway em modo simulado.
INFO LMS API rodando na porta 3000
INFO Processando cartão final 4444

POST /api/checkout (sucesso)           antes 200 | depois 200
POST /api/checkout (cartão recusado)   antes 400 | depois 400
POST /api/checkout (curso inexistente) antes 404 | depois 404
POST /api/checkout (corpo incompleto)  antes 400 | depois 400
GET  /api/admin/financial-report       antes 200 | depois 401 (sem token) | 200 (com token)
DELETE /api/users/1                    antes 200 | depois 401 (sem token) | 200 (com token)
```

Antes, o log mostrava o número inteiro do cartão e a chave do gateway, e agora mostra só os quatro últimos dígitos do cartão.

**Projeto 3** (`python seed.py` e `python app.py`)

```
  3 usuários
  4 categorias
  10 tasks
WARNING __main__: SECRET_KEY não definida; usando chave aleatória temporária (tokens não sobrevivem ao reinício).
 * Debug mode: off

GET /, /health, /tasks, /tasks/1, /tasks/search, /tasks/stats   200 | 200
GET /tasks/9999                                                 404 | 404
POST /tasks (válida | título curto)                             201 400 | 201 400
PUT /tasks/1, DELETE /tasks/2                                   200 | 200
GET /users, /users/1, /users/1/tasks, PUT /users/1              200 | 200
POST /users                                                     201 | 201
POST /login (certo | errado)                                    200 401 | 200 401
GET /reports/summary, /reports/user/1, /categories              200 | 200
POST /categories                                                201 | 201
PUT /categories/1, DELETE /categories/4                         200 | 200
DELETE /users/3                                                 200 | 401 (sem token)
```

O campo `password` aparecia em quatro respostas e agora não aparece em nenhuma. O login com as senhas originais do seed continua funcionando, e o banco continua em `instance/tasks.db`. O token também foi testado à parte: para criar um admin, a API responde 401 sem token, 403 com o token de um usuário comum e 201 com o token de um admin, e o mesmo acontece ao mudar `role` ou `active` e no `DELETE /users/<id>`.

### Comportamento da skill em cada stack

No projeto 1, um Flask com todo o código em quatro arquivos, a skill separou o código em camadas dentro de `src/`, trocou todo o SQL montado com texto por consultas com parâmetros e passou a guardar as senhas com hash scrypt. Um banco criado pela versão antiga é convertido sozinho quando a aplicação sobe. No resumo final, a skill não disse que todos os problemas tinham sido resolvidos e listou dois que ficaram: o AP-03, marcado como `(possible)`, porque as rotas de leitura e gravação continuam abertas numa API que não tem login com token, e parte do AP-11, que ficou para não mudar o status das respostas. Foi nessa execução que apareceram os dois erros corrigidos depois, o `pkill` que deixou a versão antiga respondendo na porta e o `git rm --cached` nos arquivos apagados.

No projeto 2, em Express, os callbacks encadeados viraram funções com `async/await`, o checkout e a exclusão de usuário passaram a gravar tudo ou nada numa transação, e a skill parou a aplicação sempre pelo `stop_port.sh`, sem mexer no git. Algumas respostas mudaram sem ser por segurança. O DELETE agora apaga também as matrículas e os pagamentos do usuário, responde "Usuário deletado, com suas matrículas e pagamentos." e devolve 404 para um usuário que não existe. O checkout com pagamento recusado não cria mais o usuário, e um `card` enviado como número, que antes derrubava o servidor, agora recebe 400. Essas mudanças vão contra a regra da skill, que só permite mudar uma resposta por segurança, e foram mantidas por decisão manual, como explicado em "Desafios encontrados".

No projeto 3, que já tinha parte das camadas, nada foi reescrito do zero. A lógica das rotas foi para os controllers, as contagens passaram a ser feitas pelo banco, `Query.get()` virou `db.session.get()`, e o token falso do login virou um token assinado que vale por oito horas. O `datetime.utcnow()` não entrou como deprecated, porque o projeto usa Python 3.10 e ele só ficou deprecated no 3.12, enquanto a análise manual o incluiu pensando na próxima versão. A skill seguiu a orientação dada na pausa, mas foi menos cuidadosa no resumo do que na primeira rodada: disse que não restava nenhum problema, sem avisar que o `PUT /users/<id>` ainda deixa trocar o e-mail ou a senha de outro usuário sem token.

Sobre o idioma, o agente escreveu às vezes em português e às vezes em inglês, e os títulos do relatório ficaram em inglês porque seguem o template, que copia o formato do exemplo do desafio.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (testado na versão 2.1.330)
- Python 3.10 ou superior, para os projetos 1 e 3
- Node.js e npm, para o projeto 2

### Execução da skill

A skill já está em `.claude/skills/refactor-arch/` dentro de cada projeto. Para rodá-la de novo sobre o código original, volte o projeto ao primeiro commit (`6d1ce62`) e mantenha a pasta `.claude/`.

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

A skill mostra o resumo da Fase 1 e o relatório da Fase 2 e para na pergunta `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Com "y", o relatório é gravado em `reports/audit-project-N.md` e a refatoração começa. Com "n", a execução termina sem alterar nenhum arquivo. Como a pasta `reports/` fica fora da pasta do projeto, o Claude Code pode pedir permissão para ler e gravar o relatório, e uma nova execução grava por cima do relatório anterior do mesmo projeto.

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

As requisições de `api.http` continuam funcionando, mas as duas rotas de administrador, que antes eram abertas, agora só respondem com o header `X-Admin-Token`:

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

Antes da refatoração, qualquer pessoa podia criar um admin, mudar `role` e `active` de outro usuário ou apagar uma conta com todas as tarefas dela. Agora essas operações pedem o header `Authorization: Bearer <token>`, com o token que o `/login` devolve para um admin. Com o token de um usuário comum, a resposta é 403. O cadastro comum continua aberto.

Cada projeto tem um `.env.example` com as variáveis que a aplicação lê. Se a `SECRET_KEY` não estiver definida, a aplicação cria uma chave aleatória sempre que sobe e avisa no log.
