```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: routes/user_routes.py:42, 52, 71, 92, 119-125, 134-142, 210
Description: POST /users aceita role "admin" vindo do corpo (linhas 52 e 71). PUT /users/<id> troca role e active de qualquer usuário (119-125). DELETE /users/<id> apaga o usuário e todas as tasks dele (134-142). Nenhuma dessas rotas verifica token ou sessão. O login devolve um token previsível, 'fake-jwt-token-' + str(user.id) (linha 210), que nenhuma rota confere.
Impact: Qualquer pessoa cria uma conta admin, promove ou desativa usuários e apaga contas inteiras com as tasks delas.
Recommendation: Proteger as rotas administrativas com um decorator de autenticação/admin e emitir um token assinado (playbook T03).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: models/user.py:21; routes/user_routes.py:33, 85, 129, 209
Description: User.to_dict() inclui 'password': self.password (o hash MD5). Esse dicionário é devolvido por GET /users/<id> (33), POST /users (85), PUT /users/<id> (129) e POST /login (209).
Impact: Quem chama a API recebe o hash MD5 das senhas, que se reverte com tabela pronta (ver AP-06).
Recommendation: Tirar o campo password da serialização pública (playbook T05).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: app.py:11, 13, 34; services/notification_service.py:7-10
Description: SECRET_KEY fixa 'super-secret-key-123' (app.py:13), URI do banco fixa (11) e app.run(debug=True, host='0.0.0.0') (34). A NotificationService tem email_user 'taskmanager@gmail.com' e email_password 'senha123' no código (notification_service.py:9-10). Nenhum valor vem de os.environ, embora python-dotenv esteja nas dependências.
Impact: Os segredos vão para o repositório. O modo debug, aberto em 0.0.0.0, expõe o depurador interativo do Werkzeug para a rede.
Recommendation: Ler a configuração do ambiente num módulo config.py, com debug desligado por padrão (playbook T01).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: models/user.py:29, 32; routes/user_routes.py:64, 115; seed.py:19, 26, 33
Description: set_password usa hashlib.md5(pwd.encode()).hexdigest(), sem salt, e check_password compara com ==. O mínimo exigido é 4 caracteres (user_routes.py:64, 115), e o seed grava senhas como '1234', 'abcd' e 'pass'.
Impact: Se o banco vazar, as senhas se revertem por rainbow table em segundos.
Recommendation: Usar werkzeug.security.generate_password_hash/check_password_hash, com salt (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299; routes/user_routes.py:42-90, 92-132, 185-211; routes/report_routes.py:12-101, 103-155
Description: Os handlers fazem consulta ao ORM (Model.query, db.session), validação, cálculo de atraso e estatística e serialização no mesmo corpo. summary_report tem 90 linhas e create_task 70. A pasta services/ existe, mas nenhuma rota a usa, e os métodos de regra do model (Task.validate_status, validate_priority, is_overdue) nunca são chamados.
Impact: A regra fica espalhada e repetida entre as rotas. Não dá para testar sem HTTP.
Recommendation: Criar controllers/services que concentrem a regra e deixar as rotas só com request/response (playbook T07).

### [HIGH] God Class / God File (AP-04)
File: routes/report_routes.py:157-223; routes/task_routes.py:1-299
Description: O blueprint de relatórios também contém o CRUD completo de categorias (157-223), ou seja, dois domínios num arquivo só. task_routes.py tem 299 linhas misturando acesso a dados, regra e HTTP para todas as operações de task.
Impact: Mudar categorias exige mexer no arquivo de relatórios, e cada arquivo de rota acumula responsabilidades de várias camadas.
Recommendation: Separar por domínio (categories, reports, tasks, users) e por camada (playbook T04).

### [MEDIUM] Consultas N+1 (AP-10)
File: routes/task_routes.py:42, 51; routes/user_routes.py:22; routes/report_routes.py:56, 163
Description: GET /tasks chama User.query.get e Category.query.get para cada task (42, 51). GET /users faz len(u.tasks) com lazy load por usuário (22). summary_report roda Task.query.filter_by(user_id=u.id) por usuário (56), e GET /categories faz um count por categoria (163).
Impact: O número de consultas cresce linearmente com os dados, e as rotas de listagem ficam lentas.
Recommendation: Usar joinedload/selectinload ou uma agregação com GROUP BY (playbook T10).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: routes/task_routes.py:275-287; routes/report_routes.py:19-28, 30-43, 57-61, 119-135
Description: Ficam 4 a 9 COUNTs separados por status e prioridade que caberiam num GROUP BY (task_routes 275-279, report_routes 19-28). Task.query.all() é seguido de um laço Python só para contar as atrasadas (task_routes 281-287, report_routes 30-43), e as concluídas por usuário também são contadas em Python (57-61, 119-135).
Impact: Memória e tempo crescem com a tabela tasks.
Recommendation: Mover as contagens para consultas agregadas no model (playbook T10).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: routes/task_routes.py:113, 167-169, 182, 261, 264; routes/report_routes.py:196-202; routes/user_routes.py:103, 115, 125
Description: priority não tem o tipo conferido: "priority": "alta" faz `priority < 1` lançar TypeError → 500 (113, 182). PUT /tasks com "title": null → len(None) → 500 (167). /tasks/search?priority=x → int('x') sem tratamento → 500 (261, 264). PUT /categories não trata get_json() None (196-197), e name/color não são validados (o helper is_valid_color existe e não é usado). Em PUT /users, name (103) e active (125) entram sem checagem, e password não tem o tipo conferido (115).
Impact: Corpos inválidos viram erro 500 em vez de 400, e dados inválidos chegam ao banco.
Recommendation: Centralizar a validação num schema/validador por recurso, usado tanto na criação quanto na atualização (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: routes/task_routes.py:62, 137, 151, 204, 221, 236; routes/user_routes.py:87, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88; app.py:1-34
Description: Há 13 `except:` sem tipo e 3 `except Exception as e` (em task_routes.py:221 o e nem é usado). GET /tasks engole qualquer erro num 500 genérico (62). Não existe nenhum @app.errorhandler em app.py.
Impact: Falhas reais ficam escondidas, KeyboardInterrupt/SystemExit são capturados e cada rota responde erro de um jeito.
Recommendation: Capturar exceções específicas e registrar error handlers centrais (playbook T11).

### [MEDIUM] Código duplicado (AP-14)
File: routes/task_routes.py:17-39, 71-80, 96-114, 166-184, 283-287; routes/user_routes.py:61, 106, 162-180; routes/report_routes.py:33-36, 132-135; models/task.py:23-36, 50-60; utils/helpers.py:21, 57-108
Description: A regra "está atrasada?" aparece 7 vezes (task_routes 30-39, 71-80, 283-287; user_routes 171-180; report_routes 33-36, 132-135; models/task.py:50-60). A serialização de task é refeita à mão (task_routes 17-28, user_routes 162-169) em vez de usar Task.to_dict. A validação de task é duplicada entre create (96-114), update (166-184) e helpers.process_task_data (57-108). A regex de e-mail se repete em user_routes 61 e 106 e em helpers.py:21.
Impact: Uma correção feita num lugar é esquecida nos outros, e as respostas já divergem (o campo overdue só aparece em algumas rotas).
Recommendation: Uma única implementação no model/service, reutilizada por todas as rotas (playbook T04/T07).

### [MEDIUM] Uso de API deprecated (AP-15)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213
Description: Model.query.get(id) aparece em 16 lugares. Ele é API legada no SQLAlchemy 2.0 (2.0.58 instalado) e no Flask-SQLAlchemy 3.1.1 e emite LegacyAPIWarning. datetime.utcnow() não foi reportado: o .venv usa Python 3.10, e a depreciação só existe a partir do 3.12.
Impact: Gera avisos agora e quebra numa próxima versão maior do SQLAlchemy.
Recommendation: Trocar por db.session.get(Model, id) (playbook T12).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: routes/task_routes.py:96, 99, 104, 110, 113, 167, 169, 177, 182; routes/user_routes.py:52, 64, 71, 115, 120; routes/report_routes.py:45, 129, 180; models/task.py:39, 46; utils/helpers.py:75, 110-116
Description: A lista ['pending', 'in_progress', 'done', 'cancelled'] aparece 4 vezes, e os roles 2 vezes. Os limites 3/200 (título), 1-5 (prioridade), 4 (senha), 7 dias e prioridade <= 2 estão soltos no código. As constantes VALID_STATUSES, MIN_PASSWORD_LENGTH etc. existem em helpers.py:110-116, mas ninguém as importa.
Impact: Mudar uma regra exige caçar todas as ocorrências.
Recommendation: Constantes de domínio num único módulo, usadas em todo lugar (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: routes/report_routes.py:24-28, 53-61; routes/task_routes.py:14-59; models/task.py:45; models/category.py:14; utils/helpers.py:25, 83
Description: Contadores p1..p5 (report_routes 24-28), u/t em laços longos (task_routes 14-59 usa t por 45 linhas), parâmetro p em validate_priority, d em Category.to_dict, s e p em helpers.
Impact: Fica mais difícil ler e revisar o código.
Recommendation: Usar nomes descritivos (playbook T13).

### [LOW] print no lugar de logging (AP-18)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39, 41
Description: Eventos e erros são registrados com print(f"..."), inclusive print(f"ERRO: {str(e)}") (user_routes 89).
Impact: Sem níveis nem destino configurável, os logs se perdem em produção.
Recommendation: Usar o módulo logging com um logger por módulo (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3; models/user.py:34-38; models/task.py:38-60; utils/helpers.py:3-7, 9-108; services/notification_service.py:1-48
Description: Imports agrupados e sem uso: os, sys, json (app.py:7); json, os, sys, time (task_routes:7); hashlib, json (user_routes:6); format_date, calculate_percentage, json (report_routes:7-8); json (task.py:3); os, json, sys, math, hashlib (helpers 3-7). Código que ninguém chama: NotificationService inteira, todas as funções de utils/helpers.py, Task.validate_status/validate_priority/is_overdue e User.is_admin.
Impact: Ruído, e uma falsa impressão de que existem camadas de serviço e validação.
Recommendation: Remover os imports mortos e reaproveitar ou apagar o código não usado (playbook T13).

Deprecated APIs: Model.query.get (AP-15)
================================
Total: 16 findings
================================
```
