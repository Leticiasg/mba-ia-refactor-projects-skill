# Playbook de refatoração (Fase 3)

Transformações concretas para cada anti-pattern do catálogo, com código antes/depois em Python e em JavaScript. Use os exemplos da linguagem detectada na Fase 1 e adapte nomes de tabelas, campos e mensagens ao projeto. Os exemplos mostram a técnica; não copie nomes que não existem no projeto.

Ordem sugerida na Fase 3: T04 (estrutura) → T01 (config) → T08 (conexão) → T02 / T06 / T05 / T03 (segurança) → T07 (camadas) → T09 / T10 (dados) → T11 (erros) → T12 / T13 (acabamento).

| ID | Transformação | Corrige |
|---|---|---|
| T01 | Extrair configuração para variáveis de ambiente | AP-01 |
| T02 | Consultas parametrizadas | AP-02 |
| T03 | Proteger rotas administrativas e dados de outro usuário | AP-03 |
| T04 | Quebrar God Class em Model / Controller / View | AP-04, AP-14 |
| T05 | Tirar dado sensível de respostas e logs | AP-05 |
| T06 | Hash de senha forte | AP-06 |
| T07 | Tirar regra de negócio da rota | AP-07, AP-14 |
| T08 | Trocar estado global por dependência injetada | AP-08 |
| T09 | Envolver gravações em transação | AP-09 |
| T10 | Eliminar N+1 e mover agregação para o banco | AP-10, AP-13 |
| T11 | Validação e tratamento de erro centralizado | AP-11, AP-12 |
| T12 | Substituir APIs deprecated | AP-15 |
| T13 | Constantes, nomes, logging e limpeza | AP-16 a AP-19 |

---

## T01 — Extrair configuração para variáveis de ambiente

**Python — antes**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-123"
app.config["DEBUG"] = True
```

**Python — depois** (`src/config/settings.py`)
```python
import os
import secrets
import logging

logger = logging.getLogger(__name__)

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")

if not os.environ.get("SECRET_KEY"):
    logger.warning("SECRET_KEY não definida; usando chave aleatória temporária.")
```
```python
# src/app.py
app.config.from_object(Settings)
```

**JavaScript — antes**
```js
const config = { dbPass: "senha_prod_123", paymentGatewayKey: "pk_live_abc", port: 3000 };
```

**JavaScript — depois** (`src/config/settings.js`)
```js
module.exports = {
  port: Number(process.env.PORT || 3000),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  smtpUser: process.env.SMTP_USER || '',
};
```

Crie `.env.example` com os nomes (`SECRET_KEY=troque-isto`, `PAYMENT_GATEWAY_KEY=`) e nenhum valor real.

---

## T02 — Consultas parametrizadas

**Python — antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("UPDATE pedidos SET status = '" + status + "' WHERE id = " + str(pedido_id))
```

**Python — depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
```

Busca dinâmica: monte só a estrutura com texto fixo e passe os valores à parte.
```python
query, params = "SELECT * FROM produtos WHERE 1=1", []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"
    params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    query += " AND categoria = ?"
    params.append(categoria)
cursor.execute(query, params)
```

**JavaScript — antes**
```js
db.get(`SELECT * FROM users WHERE email = '${email}'`, cb);
```

**JavaScript — depois**
```js
db.get('SELECT * FROM users WHERE email = ?', [email], cb);
```

---

## T03 — Proteger rotas administrativas e dados de outro usuário

Mantenha a rota (contrato), mas exija um token de administrador vindo do ambiente. Sem token configurado, a rota fica bloqueada. A mudança de status (200 → 401) é uma exceção de segurança e precisa constar no resumo da Fase 3.

**Python — antes**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    ...
```

**Python — depois** (`src/middlewares/auth.py`)
```python
import hmac
from functools import wraps
from flask import request, current_app, jsonify

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        received = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(received, expected):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)
    return wrapper
```
```python
@admin_bp.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_database():
    return jsonify(admin_controller.reset_database()), 200
```

**Edição de dados de um usuário.** A rota que altera ou apaga a conta de um usuário exige login e só aceita o dono da conta ou um admin, seja qual for o campo enviado. Campos que mudam privilégio (`role`, `active`) continuam exigindo admin, mesmo para o dono. Não proteja só alguns campos: com `email` e `password` liberados, qualquer pessoa toma outra conta.

**Python — antes**
```python
def update_user(user_id, data, requester):
    user = get_user(user_id)
    if "role" in data or "active" in data:   # email e password passam sem checagem
        ensure_admin(requester)
    ...
```

**Python — depois**
```python
def ensure_owner_or_admin(requester, user_id):
    if requester is None:
        raise UnauthorizedError("Não autorizado")
    if requester.id != user_id and not requester.is_admin():
        raise ForbiddenError("Sem permissão para alterar este usuário")

def update_user(user_id, data, requester):
    user = get_user(user_id)
    ensure_owner_or_admin(requester, user_id)
    if "role" in data or "active" in data:
        ensure_admin(requester)
    ...
```

**JavaScript — depois**
```js
function requireOwnerOrAdmin(req, res, next) {
  const user = req.user; // preenchido pelo middleware que valida o token
  if (!user) return res.status(401).json({ error: 'Não autorizado' });
  if (String(user.id) !== String(req.params.id) && user.role !== 'admin') {
    return res.status(403).json({ error: 'Sem permissão para alterar este usuário' });
  }
  next();
}
```

A mesma regra vale para todo registro que pertence a um usuário (pedido, tarefa, matrícula): compare o dono do registro (`task.user_id`) com quem chama. Na criação, o dono é quem chama. Ignore o `user_id` do corpo, ou só aceite outro valor de um admin. Para dados de todos (catálogo, categorias), exija admin em todos os métodos que gravam, e não só no `DELETE`.

**Login sem token.** Se o projeto tem login, mas ele não devolve token nem sessão, crie um token assinado no login (`itsdangerous` no Flask, `crypto.createHmac` no Node) e devolva-o num campo novo, mantendo os campos antigos. Campo novo não quebra o contrato. As rotas passam a ler `Authorization: Bearer <token>`.

**Projeto sem login.** Não crie rota de login, coluna de papel nem cadastro de sessão: isso é funcionalidade nova, não refatoração. Use o token de admin vindo do ambiente (exemplo acima) nas rotas de admin, e o que seria "dono ou admin" fica só para admin. Onde o corpo já traz uma senha (ex.: checkout), confira essa senha antes de agir em nome de uma conta existente.

**Uma conta existente não serve de atalho.** Se a rota cria a conta quando o e-mail é novo e usa a conta existente quando não é, confira a senha da conta existente antes de gravar em nome dela; senha errada responde 401.

Na Fase 3, confira cada rota protegida com três chamadas: sem token (401), com o token de outro usuário comum (403) e com o token do dono ou de um admin (200).

Rota que executa SQL vindo do cliente: além do token, aceite só `SELECT` e use uma conexão somente leitura (`sqlite3.connect("file:loja.db?mode=ro", uri=True)`), Não remova a rota: o contrato continua o mesmo, e o token mais a conexão somente leitura já fecham o risco.

**JavaScript — antes**
```js
app.get('/api/admin/financial-report', (req, res) => { /* devolve faturamento de todos os alunos */ });
```

**JavaScript — depois** (`src/middlewares/requireAdmin.js`)
```js
const crypto = require('crypto');
const settings = require('../config/settings');

module.exports = function requireAdmin(req, res, next) {
  const expected = Buffer.from(settings.adminToken || '');
  const received = Buffer.from(req.get('X-Admin-Token') || '');
  if (!expected.length || expected.length !== received.length || !crypto.timingSafeEqual(expected, received)) {
    return res.status(401).json({ error: 'Não autorizado' });
  }
  next();
};
```
```js
router.get('/api/admin/financial-report', requireAdmin, reportController.financialReport);
```

---

## T04 — Quebrar God Class em Model / Controller / View

**Python — antes** (um arquivo com SQL, regra e formatação de vários domínios)
```python
# models.py
def criar_pedido(usuario_id, itens):
    db = get_db(); cursor = db.cursor()
    total = 0
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        ...
def relatorio_vendas(): ...
def login_usuario(email, senha): ...
```

**Python — depois**
```python
# src/models/produto_model.py
def buscar_por_id(db, produto_id):
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return dict(row) if row else None

def baixar_estoque(db, produto_id, quantidade):
    db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))
```
```python
# src/controllers/pedido_controller.py
from src.models import produto_model, pedido_model
from src.middlewares.errors import ValidationError

def criar_pedido(db, usuario_id, itens):
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    total = 0
    for item in itens:
        produto = produto_model.buscar_por_id(db, item["produto_id"])
        if produto is None:
            raise ValidationError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]
    with db:  # T09
        pedido_id = pedido_model.inserir(db, usuario_id, total)
        for item in itens:
            pedido_model.inserir_item(db, pedido_id, item)
            produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"])
    return {"pedido_id": pedido_id, "total": total}
```
```python
# src/views/pedido_routes.py
from flask import Blueprint, request, jsonify
from src.models.database import get_db
from src.controllers import pedido_controller

pedido_bp = Blueprint("pedidos", __name__)

@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json(silent=True) or {}
    resultado = pedido_controller.criar_pedido(get_db(), dados.get("usuario_id"), dados.get("itens", []))
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201
```

**JavaScript — antes** (classe que cria o banco, registra rotas e faz o checkout)
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE ... */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* SQL + regra + resposta */ });
  }
}
```

**JavaScript — depois**
```js
// src/models/courseModel.js
module.exports = (db) => ({
  findActiveById: (id) => db.getAsync('SELECT * FROM courses WHERE id = ? AND active = 1', [id]),
});
```
```js
// src/controllers/checkoutController.js
const { NotFoundError } = require('../middlewares/errors');

module.exports = ({ courseModel, userModel, enrollmentModel, paymentService }) => ({
  async checkout({ name, email, password, courseId, card }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');
    // ... regra de negócio e transação (T09)
  },
});
```
```js
// src/views/checkoutRoutes.js
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (checkoutController) => {
  const router = express.Router();
  router.post('/api/checkout', asyncHandler(async (req, res) => {
    const { usr, eml, pwd, c_id, card } = req.body;
    const result = await checkoutController.checkout({ name: usr, email: eml, password: pwd, courseId: c_id, card });
    res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
  }));
  return router;
};
```
```js
// src/app.js (composition root)
const db = createDatabase(settings.dbPath);
const courseModel = require('./models/courseModel')(db);
const checkoutController = require('./controllers/checkoutController')({ courseModel, /* ... */ });
app.use(require('./views/checkoutRoutes')(checkoutController));
app.use(errorHandler);
app.listen(settings.port);
```

---

## T05 — Tirar dado sensível de respostas e logs

**Python — antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, "role": self.role}
```
```python
return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "debug": True})
```

**Python — depois**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "role": self.role}
```
```python
return jsonify({"status": "ok", "database": "connected"})
```

**JavaScript — antes**
```js
console.log(`Processando cartão ${card} na chave ${config.paymentGatewayKey}`);
```

**JavaScript — depois**
```js
logger.info(`Processando cartão final ${String(card).slice(-4)}`);
```

Em SQL cru, liste as colunas em vez de `SELECT *` quando a tabela tem senha.

---

## T06 — Hash de senha forte

Use o que já vem instalado: `werkzeug.security` (dependência do Flask) e o módulo `crypto` do Node.

**Python — antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
...
return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

**Python — depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

Login com SQL cru: busque pelo e-mail e confira o hash fora do SQL.
```python
row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
if row is None or not check_password_hash(row["senha"], senha):
    raise UnauthorizedError("Email ou senha inválidos")
```

**JavaScript — antes**
```js
function badCrypto(pwd) { return Buffer.from(pwd).toString('base64').substring(0, 10); }
const hash = badCrypto(p || "123456");
```

**JavaScript — depois**
```js
const crypto = require('crypto');

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, hash] = stored.split(':');
  const candidate = crypto.scryptSync(password, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```
Sem senha no corpo: responda 400 em vez de usar uma senha padrão, a menos que o contrato original aceite a requisição sem senha; nesse caso gere uma senha aleatória e registre a decisão.

Atualize o seed para gravar com o hash novo e confira que os usuários de exemplo continuam entrando com as senhas originais.

---

## T07 — Tirar regra de negócio da rota

**Python — antes**
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if len(data.get('title', '')) < 3:
        return jsonify({'error': 'Título muito curto'}), 400
    user = User.query.get(data['user_id'])
    ...
    task = Task(); task.title = data['title']; db.session.add(task); db.session.commit()
    return jsonify(task.to_dict()), 201
```

**Python — depois**
```python
# src/views/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    task = task_controller.create_task(request.get_json(silent=True) or {})
    return jsonify(task.to_dict()), 201
```
```python
# src/controllers/task_controller.py
def create_task(data):
    title = data.get('title') or ''
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if data.get('user_id') and not db.session.get(User, data['user_id']):
        raise NotFoundError('Usuário não encontrado')
    return task_model.create(title=title, user_id=data.get('user_id'), ...)
```

**JavaScript — antes**
```js
app.delete('/api/users/:id', (req, res) => {
  db.run('DELETE FROM users WHERE id = ?', [req.params.id], () => res.send('Usuário deletado'));
});
```

**JavaScript — depois**
```js
// views
router.delete('/api/users/:id', asyncHandler(async (req, res) => {
  const message = await userController.deleteUser(req.params.id);
  res.send(message);
}));
```
```js
// controller
async deleteUser(id) {
  await userModel.deleteById(id);
  return 'Usuário deletado';
}
```

Regra repetida em vários lugares (ex.: "task está atrasada") vira um método do model, usado por todos.

---

## T08 — Trocar estado global por dependência injetada

**Python — antes**
```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

**Python — depois** (`src/models/database.py`)
```python
import sqlite3
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        create_schema_and_seed(get_db())
```

**JavaScript — antes**
```js
let globalCache = {};
let totalRevenue = 0;
module.exports = { globalCache, totalRevenue };
```

**JavaScript — depois**: a dependência nasce no composition root e é passada para quem usa.
```js
// src/app.js
const db = createDatabase(settings.dbPath);
const userModel = createUserModel(db);
const userController = createUserController({ userModel });
```
Estado que ninguém lê é apagado (T13). Cache, se for necessário, vira um objeto criado no composition root e injetado.

---

## T09 — Envolver gravações em transação

**Python — antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = ...")
db.commit()
```

**Python — depois**
```python
with db:  # commit no fim; rollback automático se der exceção
    pedido_id = pedido_model.inserir(db, usuario_id, total)
    for item in itens:
        pedido_model.inserir_item(db, pedido_id, item)
        produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"])
```
SQLAlchemy: `db.session.add(...)` várias vezes e um único `db.session.commit()`; em caso de erro, `db.session.rollback()`.

**JavaScript — antes**
```js
db.run('INSERT INTO enrollments ...', [userId, cid], function (err) {
  db.run('INSERT INTO payments ...', [this.lastID, price, status], function (err) {
    db.run('INSERT INTO audit_logs ...', [...], () => res.json({ msg: 'Sucesso' }));
  });
});
```

**JavaScript — depois** (`src/models/database.js` com helpers em Promise)
```js
function createDatabase(path) {
  const db = new sqlite3.Database(path);
  db.runAsync = (sql, params = []) => new Promise((resolve, reject) =>
    db.run(sql, params, function (err) { err ? reject(err) : resolve(this); }));
  db.getAsync = (sql, params = []) => new Promise((resolve, reject) =>
    db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
  db.allAsync = (sql, params = []) => new Promise((resolve, reject) =>
    db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));
  return db;
}
```
```js
// controller
await db.runAsync('BEGIN');
try {
  const enrollment = await db.runAsync('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
  await db.runAsync('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollment.lastID, price, 'PAID']);
  await db.runAsync('INSERT INTO audit_logs (action, created_at) VALUES (?, datetime(\'now\'))', [`Checkout ${courseId}`]);
  await db.runAsync('COMMIT');
  return enrollment.lastID;
} catch (err) {
  await db.runAsync('ROLLBACK');
  throw err;
}
```

---

## T10 — Eliminar N+1 e mover agregação para o banco

**Python (SQL cru) — antes**
```python
for row in pedidos:
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"])).fetchall()
    for item in itens:
        prod = cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"])).fetchone()
```

**Python (SQL cru) — depois**
```python
rows = db.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE p.usuario_id = ?
    ORDER BY p.id
""", (usuario_id,)).fetchall()

pedidos = {}
for r in rows:
    pedido = pedidos.setdefault(r["id"], {"id": r["id"], "usuario_id": r["usuario_id"], "status": r["status"],
                                          "total": r["total"], "criado_em": r["criado_em"], "itens": []})
    if r["produto_id"] is not None:
        pedido["itens"].append({"produto_id": r["produto_id"], "produto_nome": r["produto_nome"] or "Desconhecido",
                                "quantidade": r["quantidade"], "preco_unitario": r["preco_unitario"]})
return list(pedidos.values())
```

**Python (SQLAlchemy) — antes**
```python
pending = Task.query.filter_by(status='pending').count()
done = Task.query.filter_by(status='done').count()
all_tasks = Task.query.all()
overdue = sum(1 for t in all_tasks if t.due_date and t.due_date < now and t.status not in ('done', 'cancelled'))
```

**Python (SQLAlchemy) — depois**
```python
from sqlalchemy import func

counts = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
overdue = Task.query.filter(Task.due_date < now, Task.status.notin_(['done', 'cancelled'])).count()
```

**JavaScript — antes**
```js
courses.forEach(c => {
  db.all('SELECT * FROM enrollments WHERE course_id = ?', [c.id], (err, enrollments) => {
    enrollments.forEach(enr => {
      db.get('SELECT name FROM users WHERE id = ?', [enr.user_id], (err, user) => {
        db.get('SELECT amount, status FROM payments WHERE enrollment_id = ?', [enr.id], ...);
```

**JavaScript — depois**
```js
const rows = await db.allAsync(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id`);

const report = new Map();
for (const r of rows) {
  if (!report.has(r.course_id)) report.set(r.course_id, { course: r.title, revenue: 0, students: [] });
  const entry = report.get(r.course_id);
  if (r.status === 'PAID') entry.revenue += r.amount;
  if (r.student !== null || r.amount !== null) {
    entry.students.push({ student: r.student || 'Unknown', paid: r.amount || 0 });
  }
}
return [...report.values()];
```

Confira que o formato e a ordem da resposta continuam iguais aos do baseline.

---

## T11 — Validação e tratamento de erro centralizado

**Python — antes**
```python
def buscar_produto(id):
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Python — depois** (`src/middlewares/errors.py` e `error_handler.py`)
```python
class AppError(Exception):
    status_code = 500
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ValidationError(AppError):
    status_code = 400

class UnauthorizedError(AppError):
    status_code = 401

class NotFoundError(AppError):
    status_code = 404
```
```python
from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app, error_field="erro"):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({error_field: e.message}), e.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        if isinstance(e, HTTPException):  # 404 de rota inexistente, 405 etc.
            return e
        app.logger.exception("Erro não tratado")
        return jsonify({error_field: "Erro interno do servidor"}), 500
```
Validação no controller, antes de qualquer gravação:
```python
def validar_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            raise ValidationError(f"{campo.capitalize()} é obrigatório")
    if dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
```
Use a mesma função na criação e na atualização. Leia o corpo com `request.get_json(silent=True) or {}` para corpo vazio virar 400 e não 500. Mantenha as mensagens e o nome do campo de erro do projeto original.

**JavaScript — antes**
```js
db.run('INSERT INTO audit_logs ...', [...], (err) => { res.json({ msg: 'Sucesso' }); });
```

**JavaScript — depois**
```js
// src/middlewares/asyncHandler.js — Express 4 não captura Promise rejeitada sozinho
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
```
```js
// src/middlewares/errorHandler.js
const { AppError } = require('./errors');

module.exports = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  console.error(err);
  res.status(500).send('Erro interno do servidor');
};
```
```js
// src/app.js — depois de todas as rotas
app.use(errorHandler);
```
Use `res.send` (texto) ou `res.json` conforme o formato de erro que o projeto já devolvia.

---

## T12 — Substituir APIs deprecated

**Python — antes**
```python
user = User.query.get(user_id)
task = Task.query.get_or_404(task_id)
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if t.due_date < datetime.utcnow(): ...
```

**Python — depois**
```python
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # mantém datetimes "ingênuos" como os já gravados

user = db.session.get(User, user_id)
task = db.get_or_404(Task, task_id)
created_at = db.Column(db.DateTime, default=utcnow)
if t.due_date < utcnow(): ...
```
O `.replace(tzinfo=None)` evita erro ao comparar com datas já gravadas sem fuso. Se o projeto já guarda datas com fuso, remova o `replace`.

**JavaScript — antes**
```js
const buf = new Buffer(data);
const { pathname } = url.parse(req.url);
res.send(404);
```

**JavaScript — depois**
```js
const buf = Buffer.from(data);
const { pathname } = new URL(req.url, `http://${req.headers.host}`);
res.sendStatus(404);
```

A tabela completa de substituições está em `anti-patterns.md`, AP-15.

---

## T13 — Constantes, nomes, logging e limpeza

**Python — antes**
```python
import os, sys, json, datetime

if faturamento > 10000:
    desconto = faturamento * 0.1
cursor2 = db.cursor()
print("ERRO: " + str(e))
```

**Python — depois**
```python
import logging
from src.config.settings import FAIXAS_DESCONTO  # [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

logger = logging.getLogger(__name__)

desconto = next((faturamento * taxa for limite, taxa in FAIXAS_DESCONTO if faturamento > limite), 0)
itens_cursor = db.cursor()
logger.error("Falha ao criar pedido", exc_info=True)
```

**JavaScript — antes**
```js
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');
console.log(`[LOG] Salvando no cache: ${key}`);
```

**JavaScript — depois**
```js
const { usr: name, eml: email, card: cardNumber } = req.body;
const settings = require('../config/settings');
const logger = require('../config/logger'); // wrapper com níveis sobre console
logger.debug(`Cache atualizado: ${key}`);
```

Regras:
- Números e listas de domínio vão para `config/` com nome (`TITLE_MIN_LENGTH = 3`, `VALID_STATUSES = [...]`) e são importados onde forem usados.
- Uma letra só em índice de laço curto.
- Nada de nome que esconda função nativa (`id` → `produto_id`).
- Imports um por linha; apague os não usados e as variáveis exportadas que ninguém lê.
- Logging com níveis (`logging` no Python; um wrapper simples sobre `console` no Node se não houver biblioteca instalada).
