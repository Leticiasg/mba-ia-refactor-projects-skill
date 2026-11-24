# Catálogo de anti-patterns (Fase 2)

Cada anti-pattern tem um ID, uma severidade, sinais de detecção em Python e em JavaScript e a transformação do playbook que o corrige (`refactoring-playbook.md`).

**Seções:** Regras de uso (com a escala de severidade) · Resumo (tabela de AP-01 a AP-19) · CRITICAL · HIGH · MEDIUM · LOW.

## Regras de uso

- Só reporte o que você viu no código. Todo finding precisa de `arquivo:linha` exato.
- Quando o mesmo anti-pattern aparece em vários lugares, faça **um** finding e liste todas as linhas (`models.py:28, 48-49, 110`).
- Um trecho pode cair em dois anti-patterns (ex.: SQL concatenado dentro de uma God Class). Reporte os dois, cada um com sua linha.
- Audite a própria auditoria antes de fechar a lista: volte ao código de cada finding e classifique como **real** (o código comprova), **falso positivo** (retire da lista) ou **possível** (a evidência é parcial, por exemplo depende de configuração externa ou de como a rota é chamada). Um finding possível continua no relatório, marcado como possível, e diz o que falta confirmar.
- Em caso de dúvida entre duas severidades, use a escala abaixo e escolha a que descreve o pior efeito real naquele código.

### Escala de severidade

- **CRITICAL:** falha de segurança ou de arquitetura grave: expõe dados sensíveis, permite tomar o controle do banco ou mistura banco, regra de negócio e rotas no mesmo arquivo/classe.
- **HIGH:** violação forte de MVC ou SOLID que dificulta muito manter e testar: regra de negócio na rota, acoplamento sem injeção de dependência, estado global mutável, dados inconsistentes.
- **MEDIUM:** padronização, duplicação ou performance moderada: N+1, validação ausente, erro tratado de forma genérica, API deprecated.
- **LOW:** legibilidade: nomes ruins, magic numbers, `print` no lugar de log, código morto.

## Resumo

| ID | Anti-pattern | Severidade | Playbook |
|---|---|---|---|
| AP-01 | Credenciais e configuração hardcoded | CRITICAL | T01 |
| AP-02 | SQL Injection | CRITICAL | T02 |
| AP-03 | Endpoint sensível sem autenticação | CRITICAL | T03 |
| AP-04 | God Class / God File | CRITICAL | T04 |
| AP-05 | Dado sensível exposto em resposta ou log | CRITICAL | T05 |
| AP-06 | Senha guardada sem hash forte | HIGH | T06 |
| AP-07 | Regra de negócio e acesso a dados na rota | HIGH | T07 |
| AP-08 | Estado global mutável | HIGH | T08 |
| AP-09 | Várias gravações sem transação | HIGH | T09 |
| AP-10 | Consultas N+1 | MEDIUM | T10 |
| AP-11 | Validação de entrada ausente ou inconsistente | MEDIUM | T11 |
| AP-12 | Tratamento de erro genérico ou ignorado | MEDIUM | T11 |
| AP-13 | Processamento em memória do que o banco faz | MEDIUM | T10 |
| AP-14 | Código duplicado | MEDIUM | T04 / T07 |
| AP-15 | Uso de API deprecated | MEDIUM | T12 |
| AP-16 | Magic numbers e strings de domínio soltas | LOW | T13 |
| AP-17 | Nomes pouco expressivos | LOW | T13 |
| AP-18 | `print` / `console.log` no lugar de logging | LOW | T13 |
| AP-19 | Imports sem uso e código morto | LOW | T13 |

---

## CRITICAL

### AP-01 — Credenciais e configuração hardcoded

Segredos e configuração de ambiente escritos no código-fonte.

Sinais:
- Python: `SECRET_KEY = "..."`, `app.config["SECRET_KEY"] = "..."`, `password = "..."`, `email_password = '...'`, `DEBUG = True` ou `app.run(debug=True)` fixos.
- JavaScript: objetos de config com `dbPass: "..."`, `apiKey`, `paymentGatewayKey`, `secret`; chaves com prefixo `pk_live_`, `sk_live_`, `AKIA`.
- Qualquer string atribuída a nome com `key`, `secret`, `pass`, `password`, `token`, `credential`.
- URL de banco com usuário e senha embutidos.

Impacto: o segredo vai para o repositório e para qualquer cópia do código. O modo debug em produção expõe o depurador para a rede.

### AP-02 — SQL Injection

SQL montado juntando texto com dados que vêm de fora.

Sinais:
- Python: `cursor.execute("... " + x)`, `execute(f"... {x}")`, `execute("... %s" % x)`, `"...".format(x)` dentro de SQL.
- JavaScript: `` db.run(`... ${x}`) ``, `db.query("... " + req.body.x)`.
- Parâmetros de rota, query string ou corpo chegando até essas strings sem passar por `?` / `%s` / placeholders.

Não é SQL Injection: placeholders (`execute("... WHERE id = ?", (id,))`, `db.get("... = ?", [x])`) e ORM com filtros (`Model.query.filter_by(x=y)`).

Impacto: o cliente muda a consulta. Ex.: `' OR '1'='1` no login entra sem senha.

### AP-03 — Endpoint sensível sem autenticação

Rota que executa operação administrativa ou destrutiva, ou que altera dados de um usuário, sem verificar quem chama.

Sinais:
- Rotas com `admin`, `reset`, `query`, `debug`, `internal` no caminho, ou `DELETE` em massa.
- Handler que executa SQL recebido no corpo (`cursor.execute(dados["sql"])`).
- Rota que altera ou apaga a conta de um usuário pelo id (`PUT`/`PATCH`/`DELETE` em `/users/<id>`, troca de e-mail ou de senha) sem confirmar que quem chama é o dono da conta ou um admin.
- Proteção parcial: a checagem só roda para alguns campos (ex.: exige admin quando o corpo traz `role` ou `active`, mas deixa passar `email` e `password`). Trate como se não houvesse proteção.
- Ausência de decorator, middleware ou checagem de token/sessão antes da operação.

Impacto: qualquer pessoa lê, altera ou apaga dados. Trocar o e-mail ou a senha de outra conta, inclusive a de um admin, permite tomar essa conta.

### AP-04 — God Class / God File

Um arquivo ou classe com responsabilidades de várias camadas ou de vários domínios.

Sinais:
- Mesmo arquivo/classe com conexão ou SQL **e** regra de negócio **e** registro de rotas/HTTP (ex.: classe com `initDb()` e `setupRoutes(app)`).
- Arquivo de "models" com funções de vários domínios (produtos, usuários, pedidos, relatórios) misturando SQL, cálculo e formatação.
- Mais de ~300 linhas cobrindo mais de um domínio.

Severidade: CRITICAL quando junta banco + regra + rotas. HIGH quando junta só duas camadas ou vários domínios na mesma camada.

Impacto: qualquer mudança mexe em tudo; nada se testa isolado.

### AP-05 — Dado sensível exposto em resposta ou log

Sinais:
- Serialização que inclui `password`, `senha`, `pass`, hash de senha, `secret_key`, tokens (`to_dict()` com `'password'`, `SELECT *` virando JSON).
- Rota de health/status que devolve config interna (`secret_key`, `debug`, caminho do banco).
- Log com cartão, senha, chave: `console.log(\`... ${card} ... ${config.key}\`)`, `print("... " + senha)`.
- Mensagem de erro com `str(e)` ou stack trace devolvida ao cliente (ver também AP-12).

Impacto: credenciais e dados pessoais vazam para quem chama a API ou lê os logs.

---

## HIGH

### AP-06 — Senha guardada sem hash forte

Sinais:
- Senha gravada em texto puro (INSERT direto do valor recebido; seed com senhas legíveis).
- `hashlib.md5(`, `hashlib.sha1(`, `sha256` sem salt; `Buffer.from(pwd).toString('base64')`; "hash" feito à mão em loop.
- Comparação de senha com `==` sobre o valor puro.
- Senha padrão quando o cliente não envia (`pwd || "123456"`).

Impacto: se o banco vazar, as senhas vazam junto. MD5 e base64 se revertem com tabela pronta ou decodificação.

### AP-07 — Regra de negócio e acesso a dados na rota

A camada HTTP faz o trabalho do controller e do model.

Sinais:
- Handler de rota com consultas (`Model.query`, `cursor.execute`, `db.get`) **e** validação **e** cálculo no mesmo corpo.
- Handler com mais de ~30 linhas.
- Efeitos colaterais na rota: notificação, e-mail, cálculo de desconto.
- Controller importando a conexão direto (`from database import get_db`) em vez de chamar um model.
- Pasta `services/` existe, mas as rotas não a usam.

Impacto: regra repetida entre rotas, impossível testar sem HTTP, troca de banco exige mexer nas rotas.

### AP-08 — Estado global mutável

Sinais:
- Python: `db_connection = None` no módulo + `global db_connection`; `sqlite3.connect(..., check_same_thread=False)` compartilhada; listas/dicts de módulo alterados por handlers.
- JavaScript: `let cache = {}` / `let total = 0` exportados e alterados; conexão criada no construtor de uma classe que todos usam.

Impacto: requisições simultâneas interferem umas nas outras; testes dependem da ordem.

### AP-09 — Várias gravações sem transação

Sinais:
- Sequência de `INSERT`/`UPDATE` que forma uma operação só (pedido + itens + estoque; matrícula + pagamento) sem `BEGIN`/`COMMIT`/`ROLLBACK` ou `with conn:`.
- Callbacks aninhados em que cada um grava e o erro de um não desfaz os anteriores.
- `return` de erro no meio do laço depois de gravações já feitas.

Impacto: dados inconsistentes (matrícula sem pagamento, estoque baixado sem pedido).

---

## MEDIUM

### AP-10 — Consultas N+1

Sinais:
- Consulta dentro de laço sobre o resultado de outra consulta (`for row in rows: cursor.execute(...)`, `courses.forEach(c => db.all(...))`).
- Acesso a relacionamento do ORM dentro de laço (`for u in users: Task.query.filter_by(user_id=u.id)`).
- `Model.query.get(t.user_id)` dentro de laço de listagem.

Impacto: o número de consultas cresce com os dados; a rota fica lenta.

### AP-11 — Validação de entrada ausente ou inconsistente

Sinais:
- Campo do corpo usado sem checagem (`dados["preco"]`, `req.body.x` direto no SQL ou em cálculo).
- `request.get_json()` usado sem tratar `None` (corpo vazio vira erro 500).
- Criação valida um campo e a atualização do mesmo recurso não valida.
- Tipos não conferidos (`int(...)` sem tratar erro; comparação de string com número).

Impacto: dados inválidos no banco e erro 500 onde deveria ser 400.

### AP-12 — Tratamento de erro genérico ou ignorado

Sinais:
- `try/except Exception as e: return jsonify({"erro": str(e)}), 500` repetido em todos os handlers.
- Callback que recebe `err` e não usa (`(err) => { res.send(...) }`).
- Acesso a resultado sem checar erro (`enrollments.length` quando `err` veio preenchido).
- Nenhum `@app.errorhandler` / middleware de erro `(err, req, res, next)`.

Impacto: detalhes internos vazam; falhas passam em silêncio ou derrubam o processo.

### AP-13 — Processamento em memória do que o banco faz

Sinais:
- `Model.query.all()` seguido de laço só para contar ou somar.
- Várias consultas `COUNT` separadas que caberiam num `GROUP BY`.
- Filtro aplicado em Python/JS depois de trazer a tabela inteira.

Impacto: memória e tempo crescem com a tabela.

### AP-14 — Código duplicado

Sinais:
- Duas funções com corpo igual ou quase igual (mudando só o `WHERE`).
- Mapeamento linha → dicionário repetido em várias funções.
- A mesma regra (ex.: "está atrasada?") reimplementada em vários arquivos.

Impacto: uma correção feita num lugar e esquecida no outro.

### AP-15 — Uso de API deprecated

Uso de API marcada como obsoleta ou legada pela linguagem, framework ou biblioteca. Confira a versão instalada antes de reportar e sempre indique o substituto.

| Stack | Deprecated | Substituto moderno |
|---|---|---|
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` (legado) | `db.session.get(Model, id)` |
| Flask-SQLAlchemy 3.x | `Model.query.get_or_404(id)` | `db.get_or_404(Model, id)` |
| Python 3.12+ | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| Flask 2.3+ | `@app.before_first_request` (removido) | inicializar dentro de `create_app()` |
| Flask 2.3+ | `app.config["JSON_AS_ASCII"]`, `flask.json.JSONEncoder` (removidos) | `app.json.ensure_ascii`, provider em `app.json` |
| Flask 3.0+ | `from flask import Markup, escape` (removidos) | `from markupsafe import Markup, escape` |
| Python | `pkg_resources` | `importlib.metadata` / `importlib.resources` |
| Node.js | `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` |
| Node.js | `url.parse(str)` (legado) | `new URL(str)` |
| Node.js | `fs.exists(` | `fs.existsSync(` / `fs.promises.access(` |
| Node.js | `util.isArray(` | `Array.isArray(` |
| Node.js 22+ | `crypto.createCipher(` (removido) | `crypto.createCipheriv(` |
| Express 4 | `res.send(200)`, `res.json(200, obj)` | `res.sendStatus(200)`, `res.status(200).json(obj)` |
| Express 4 | `req.param('x')`, `app.del(` | `req.params.x` / `req.body.x` / `req.query.x`, `app.delete(` |
| Express 4 | `bodyParser()` sem método | `express.json()` / `express.urlencoded()` |

Impacto: a próxima atualização da dependência quebra o código ou gera avisos.

---

## LOW

### AP-16 — Magic numbers e strings de domínio soltas

Sinais:
- Números de regra de negócio no meio do código (`if faturamento > 10000: desconto = faturamento * 0.1`, `len(password) < 4`, `priority > 5`).
- Listas de status/categorias repetidas em vários arquivos (`['pending', 'in_progress', 'done', 'cancelled']`).

### AP-17 — Nomes pouco expressivos

Sinais:
- Variáveis de uma letra fora de laços curtos (`u`, `e`, `p`, `cc`, `cid`).
- Numeração em vez de nome (`cursor2`, `cursor3`, `data2`).
- Nomes que escondem funções nativas (`id`, `type`, `list`, `input` em Python).
- Nomes que não dizem o que a função faz (`badCrypto`, `doStuff`, `AppManager`).

### AP-18 — `print` / `console.log` no lugar de logging

Sinais: `print(` ou `console.log(` em handlers para registrar erro, evento ou "envio" de e-mail/SMS. Não há níveis, nem destino configurável.

### AP-19 — Imports sem uso e código morto

Sinais: módulo importado e nunca usado no arquivo; variável exportada e nunca lida; função que ninguém chama; imports agrupados numa linha (`import os, sys, json`).
