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

A skill nem sempre seguiu essa regra. Em algumas rodadas, ela também mudou respostas que não tinham a ver com segurança. Na rodada final, no projeto 1, o `PUT /pedidos/<id>/status` de um pedido que não existe passou de 200 para 404, e um e-mail repetido no cadastro passou a dar 400. No projeto 2, a mensagem do DELETE, que dizia que os dados do usuário apagado "ficaram sujos no banco", virou "Usuário deletado", porque agora as matrículas e os pagamentos são apagados junto. A skill avisou de todas essas mudanças no resumo final, e elas foram mantidas. A regra da skill continua a mesma, ou seja, manter essas mudanças foi uma decisão manual, e não algo que a skill permite.

No Flask-SQLAlchemy, um banco SQLite com caminho relativo é criado na pasta `instance/`, ao lado do código da aplicação. Se a aplicação muda de pasta, o banco vai junto sem nenhum aviso. Por isso as guidelines mandam fixar o caminho do banco e rodar o seed de novo para conferir que os dados continuam no mesmo lugar.

Dois cuidados com tratamento de erro entraram no playbook. O Express 4 não captura erros de funções `async`, então o exemplo traz um `asyncHandler` junto com o middleware de erro. No Flask, um `errorhandler(Exception)` transformaria o 404 de uma rota que não existe em erro 500, então o exemplo deixa os erros HTTP passarem.

Na primeira rodada, o Claude Code entrou em auto mode e parou logo depois do primeiro comando, e bastou digitar "continue" para seguir. Na segunda, a execução parou depois do "y" esperando uma permissão, porque a pasta `reports/` fica na raiz do repositório, fora da pasta do projeto, e o Claude Code pergunta antes de ler ou gravar arquivos fora dela.

No projeto 3, o relatório apontou o `POST /users` como rota sem autenticação, já que qualquer pessoa podia se cadastrar como admin, mas bloquear a rota inteira impediria o cadastro comum. Por isso, nas duas primeiras rodadas, o "y" da pausa veio junto com uma orientação: manter o cadastro aberto e exigir token só para criar admin, para mudar `role` ou `active` e para o `DELETE /users/<id>`. A skill fez o que foi pedido, mas a orientação deixou uma brecha. O `PUT /users/<id>` só pedia token quando o corpo trazia `role` ou `active`, então qualquer pessoa ainda podia trocar o e-mail ou a senha de outra conta, inclusive a de um admin, e entrar nela. A regra AP-03 e a correção T03 foram ampliadas para cobrir qualquer mudança nos dados de outro usuário.

Ao revisar as rotas dos três projetos depois dessa correção, apareceram outras brechas do mesmo tipo, que a regra ainda deixava passar. No projeto 3, o `PUT /tasks/<id>` continuava aberto, enquanto o `DELETE` da mesma task pedia o dono. No projeto 1, qualquer pessoa mudava o status do pedido de outra pessoa e criava pedido em nome de qualquer `usuario_id`. No projeto 2, o checkout com o e-mail de uma conta existente ignorava a senha e matriculava essa conta. A causa era a mesma: a regra falava da conta do usuário, mas não do que pertence a ele, e nada obrigava a skill a olhar todas as rotas que gravam dados. Por isso a Fase 2 ganhou um mapa de acesso, com todas essas rotas, e os três projetos foram refeitos com a regra nova. Nessa rodada final, o "y" foi dado sem orientação nenhuma.

Também foi preciso definir até onde vai o AP-03. Numa primeira tentativa, o relatório do projeto 1 recomendou fechar as leituras, como `GET /usuarios` e `GET /pedidos`, e remover a rota que executa SQL. A regra ficou assim: o AP-03 cobre as rotas de admin e as que gravam dados. Leituras comuns continuam abertas, como no original, e aparecem no resumo final como risco que ficou. A rota de SQL continua existindo, com token de admin e só leitura. No projeto 2, que não tem login, a primeira recomendação foi criar um sistema de login, e a regra passou a dizer que, nesse caso, a skill usa um token de admin vindo do ambiente e não cria login, porque isso seria uma funcionalidade nova, e não uma refatoração.

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
| No projeto 3, o `PUT /users/<id>` só pedia token quando o corpo trazia `role` ou `active`, e qualquer pessoa trocava o e-mail ou a senha de outra conta | O AP-03 passou a incluir qualquer rota que grava dados de um usuário, ou seja, a conta e tudo o que pertence a ela, como pedido, tarefa e matrícula, além das ações feitas em nome de outra pessoa. Proteger só alguns campos, ou só alguns métodos da mesma rota, passou a contar como não proteger. O T03 ganhou exemplos de "dono ou admin" | Quem troca o e-mail ou a senha de outra pessoa passa a entrar na conta dela, e quem edita o pedido ou a tarefa de outra pessoa estraga os dados dela |
| A regra ampliada ainda deixou passar rotas parecidas, como o `PUT /tasks/<id>` e o `PUT /pedidos/<id>/status` | A Fase 2 ganhou um mapa de acesso: uma tabela com todas as rotas que gravam dados e as de admin, de quem é o dado, quem pode chamar hoje e quem deveria poder. Na Fase 3, cada rota protegida é testada sem token, com o token de outro usuário e com o token do dono | Listar todas as rotas obriga a skill a responder "quem pode chamar" para cada uma, em vez de procurar só os casos que ela lembra |
| A skill recomendou fechar leituras, remover a rota de SQL e, num projeto sem login, criar um sistema de login | O AP-03 cobre rotas de admin e rotas que gravam. Leituras comuns ficam abertas e aparecem no resumo como risco. A rota de SQL fica com token e só leitura. Projeto sem login usa token de admin vindo do ambiente | Fechar leituras e criar login mudariam muito o contrato da API e acrescentariam funcionalidade nova, o que foge de uma refatoração |
| Com Python e JavaScript no mesmo playbook, o agente lê os exemplos das duas linguagens mesmo quando o projeto usa só uma | O playbook chegou a ser dividido em um arquivo por linguagem, e a divisão foi desfeita | As correções são as mesmas em qualquer linguagem, e um arquivo só deixa claro que a skill não depende de uma stack |

Ficou um limite no script de comparação: quando a resposta é um texto, e não um JSON, o `run_requests.sh` registra só a palavra `text`. Por isso a mudança na mensagem do DELETE do projeto 2 não apareceu como diferença no script, só no resumo da skill e no baseline.

Depois desses ajustes, os três projetos voltaram ao código original e foram refatorados de novo.

## Resultados

Os resultados abaixo são da rodada final, feita com a versão final da skill a partir do código original de cada projeto.

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
src/utils.js                  src/config/             # settings, constants, logger
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
utils/                        controllers/            # task, user, category, report, validators, permissions, metrics
                              middlewares/            # errors, error_handler, auth
                              services/notification_service.py
```

No projeto 3, a skill não criou a pasta `src/`, porque `models/` e `routes/` já existiam. A pasta `routes/` passou a fazer o papel das views, as camadas que faltavam foram criadas e as categorias saíram do arquivo de relatórios para um arquivo próprio. A pasta `services/` ficou, agora lendo os dados do SMTP da configuração. A `utils/` foi apagada, porque nenhuma das funções dela era usada, e as constantes foram para `config/constants.py`.

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
| Endpoints originais respondem | Sim (14 de 23 com o mesmo status; as gravações em produtos e pedidos e as 2 rotas `/admin` passaram a exigir token) | Sim (4 de 4 no checkout; relatório e DELETE passaram a exigir token) | Sim (16 de 25 com o mesmo status; todas as rotas que gravam em tasks, usuários e categorias passaram a exigir token, menos o cadastro comum) |

Os números da última linha vêm do baseline. Todas as chamadas diferentes são rotas que agora respondem 401 sem token. Com o token de admin, o baseline volta a dar exatamente os mesmos status de antes da refatoração: 23 de 23 no projeto 1, 7 de 7 no projeto 2 e 25 de 25 no projeto 3. Além do baseline, cada rota protegida foi testada à parte sem token (401), com o token de outro usuário (403) e com o token do dono ou de um admin (2xx), e todas passaram.

### Logs das aplicações após a refatoração

Os scripts do baseline rodaram de novo com o banco recriado e com o mesmo comando de antes, e nos três projetos a aplicação subiu sem nenhum erro.

**Projeto 1** (`python app.py`)

```
WARNING src.app: SECRET_KEY não definida: usando chave aleatória (tokens expiram a cada reinício).
WARNING src.models.seed: SEED_ADMIN_PASSWORD não definida: o usuário admin foi criado com senha aleatória e não poderá fazer login.
INFO src.models.seed: Banco populado com dados de exemplo
INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Debug mode: off

GET /, /health, /produtos, /produtos/busca, /produtos/1         200 | 200
GET /produtos/9999                                              404 | 404
GET /usuarios, /usuarios/1                                      200 | 200
POST /usuarios                                                  201 | 201
POST /login (certo | errado)                                    200 401 | 200 401
GET /pedidos, /pedidos/usuario/2, /relatorios/vendas            200 | 200
POST /produtos (3 casos), PUT /produtos/1, DELETE /produtos/3   400 201 400 200 200 | 401 (sem token)
POST /pedidos, PUT /pedidos/1/status                            201 200 | 401 (sem token)
POST /admin/query, POST /admin/reset-db                         200 200 | 401 (sem token)
```

O login agora devolve um campo novo, `token`, e as rotas protegidas leem o header `Authorization: Bearer <token>`. Nos testes à parte, uma cliente não conseguiu mexer em produtos, nem no pedido de outra pessoa, nem nas rotas `/admin` (403). O dono do pedido conseguiu criá-lo e cancelá-lo, mas não marcá-lo como aprovado, o que só um admin faz. O `/admin/query`, com o token de admin, recusou um `DELETE` (400), porque só aceita `SELECT`. Quem se cadastra com `"tipo":"admin"` vira cliente comum. As respostas também perderam campos por segurança: o `/usuarios` não devolve mais a `senha`, e o `/health` não mostra mais `secret_key`, `debug` e `db_path`.

**Projeto 2** (`npm start`)

```
[INFO] LMS API rodando na porta 3000
[INFO] Processando cartão final 4444 no valor 497

POST /api/checkout (sucesso)           antes 200 | depois 200
POST /api/checkout (cartão recusado)   antes 400 | depois 400
POST /api/checkout (curso inexistente) antes 404 | depois 404
POST /api/checkout (corpo incompleto)  antes 400 | depois 400
GET  /api/admin/financial-report       antes 200 | depois 401 (sem token) | 200 (com token)
DELETE /api/users/1                    antes 200 | depois 401 (sem token) | 200 (com token)
```

Antes, o log mostrava o número inteiro do cartão e a chave do gateway, e agora mostra só os quatro últimos dígitos do cartão. O checkout também foi testado à parte com o e-mail de uma conta que já existe: com a senha errada ou sem senha, a resposta é 401, e com a senha certa, 200.

**Projeto 3** (`python seed.py` e `python app.py`)

```
SECRET_KEY não definida; usando chave aleatória temporária (tokens expiram a cada reinício).
Seed concluído com sucesso!
3 usuários
4 categorias
10 tasks
 * Debug mode: off

GET /, /health, /tasks, /tasks/1, /tasks/search, /tasks/stats   200 | 200
GET /tasks/9999                                                 404 | 404
GET /users, /users/1, /users/1/tasks                            200 | 200
POST /users                                                     201 | 201
POST /login (certo | errado)                                    200 401 | 200 401
GET /reports/summary, /reports/user/1, /categories              200 | 200
POST /tasks (válida | título curto), PUT /tasks/1               201 400 200 | 401 (sem token)
PUT /users/1                                                    200 | 401 (sem token)
POST /categories, PUT /categories/1                             201 200 | 401 (sem token)
DELETE /tasks/2, DELETE /categories/4, DELETE /users/3          200 | 401 (sem token)
```

O campo `password` aparecia em quatro respostas e agora não aparece em nenhuma. O login com as senhas originais do seed continua funcionando, e o banco continua em `instance/tasks.db`. Nos testes à parte, todas as rotas que gravam responderam 401 sem token e 403 com o token de outro usuário, inclusive o `PUT /users/1` tentando trocar a senha do admin. A dona de uma task conseguiu editá-la (200), mas não passá-la para outra pessoa (403), e criou uma task para si mesma (201). Ela também mudou o próprio nome (200), mas não o próprio `role` (403). Só um admin consegue mexer em categorias. Depois dos testes, o admin continuou entrando com a senha original, ou seja, ninguém conseguiu trocá-la.

### Comportamento da skill em cada stack

No projeto 1, um Flask com todo o código em quatro arquivos, a skill separou o código em camadas dentro de `src/`, trocou todo o SQL montado com texto por consultas com parâmetros e passou a guardar as senhas com hash. O login, que só devolvia os dados do usuário, ganhou um token assinado, e as rotas de produtos, pedidos e `/admin` passaram a usar esse token. A senha do admin do seed passou a vir da variável `SEED_ADMIN_PASSWORD`. No primeiro ciclo de validação, a skill achou um erro 500 no `/admin/query` quando o SQL trazia dois comandos, corrigiu e validou de novo. No resumo final, ela listou os riscos que ficaram: as leituras de usuários e pedidos continuam abertas e mostram e-mails e pedidos de outras pessoas, e o `/admin/query`, mesmo só para admin e só leitura, permite ler o banco inteiro, inclusive as senhas, que agora estão guardadas com hash.

No projeto 2, em Express, os callbacks encadeados viraram funções com `async/await`, e o checkout e a exclusão de usuário passaram a gravar tudo ou nada numa transação. Como o projeto não tem login, o relatório e o DELETE passaram a pedir o header `X-Admin-Token`, com o valor da variável `ADMIN_TOKEN`, e o checkout passou a conferir a senha quando o e-mail já tem conta. O DELETE agora apaga também as matrículas e os pagamentos do usuário, e por isso o relatório financeiro deixou de mostrar alunos "Unknown". A skill avisou que isso apaga o histórico financeiro desse usuário e sugeriu anonimizar o usuário, em vez de apagar, se esse histórico for necessário. O checkout com pagamento recusado não cria mais o usuário, e um `card` enviado como número, que antes derrubava o servidor, agora recebe 400.

No projeto 3, que já tinha parte das camadas, nada foi reescrito do zero. A lógica das rotas foi para os controllers, as contagens passaram a ser feitas pelo banco, `Query.get()` virou `db.session.get()`, e o token falso do login virou um token assinado que vale por 24 horas. O `datetime.utcnow()` não entrou como deprecated, porque o projeto usa Python 3.10 e ele só ficou deprecated no 3.12, enquanto a análise manual o incluiu pensando na próxima versão. Sem orientação na pausa, a skill montou o mapa de acesso e protegeu todas as rotas que gravam: tasks e usuários aceitam só o dono ou um admin, e categorias só um admin. O cadastro comum continua aberto, e só um admin cria outro admin. O role `manager`, que não tinha nenhum privilégio no código original, é tratado como usuário comum.

Sobre o idioma, o agente escreveu às vezes em português e às vezes em inglês, e os títulos do relatório ficaram em inglês porque seguem o template, que copia o formato do exemplo do desafio.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (testado na versão 2.1.331)
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
SEED_ADMIN_PASSWORD=uma-senha-de-teste .venv/bin/python app.py
```

```bash
curl -i http://localhost:5000/produtos                      # 200
curl -i http://localhost:5000/usuarios                      # 200, sem o campo senha
curl -i -X POST http://localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","senha":"123456"}'          # 200
curl -i -X PUT http://localhost:5000/pedidos/1/status -H 'Content-Type: application/json' \
  -d '{"status":"cancelado"}'                               # 401, sem token
curl -i -X POST http://localhost:5000/admin/reset-db        # 401, sem token
```

O login devolve um `token`. Com o header `Authorization: Bearer <token>`, um cliente cria e cancela os próprios pedidos, e o admin (`admin@loja.com`, com a senha definida em `SEED_ADMIN_PASSWORD`) mexe em produtos, muda o status de qualquer pedido e usa as rotas `/admin`.

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
curl -i -X POST http://localhost:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Outra pessoa","eml":"gui@fullcycle.com.br","pwd":"chute","c_id":1,"card":"4111222233334444"}'   # 401, senha errada
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
curl -i -X PUT http://localhost:5000/users/1 -H 'Content-Type: application/json' \
  -d '{"password":"outrasenha"}'                            # 401, sem token
```

Antes da refatoração, qualquer pessoa podia criar um admin, mudar os dados ou as tarefas de qualquer usuário e mexer nas categorias. Agora todas as rotas que gravam pedem o header `Authorization: Bearer <token>`, com o token que o `/login` devolve. Tasks e usuários só aceitam o dono ou um admin, categorias só aceitam admin, e só um admin muda `role` e `active` ou cria outro admin. Com o token de outro usuário, a resposta é 403. O cadastro comum continua aberto.

Cada projeto tem um `.env.example` com as variáveis que a aplicação lê. Se a `SECRET_KEY` não estiver definida, a aplicação cria uma chave aleatória sempre que sobe e avisa no log.
