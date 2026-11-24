```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: routes/user_routes.py:52, 71-72, 92-132, 134-151, 210; routes/task_routes.py:225-238; routes/report_routes.py:211-223
Description: Nenhuma rota verifica quem chama. PUT /users/<id> troca email, password, role e active de qualquer conta (102-125); DELETE /users/<id> apaga qualquer usuário e as tasks dele; POST /users aceita role 'admin' vindo do corpo (52, 71). O login devolve 'fake-jwt-token-' + str(user.id) (210), um token previsível que nenhuma rota confere.
Impact: Qualquer pessoa cria um admin, troca a senha ou o e-mail de outra conta (inclusive de um admin) e a toma, ou apaga usuários, tasks e categorias.
Recommendation: Emitir token assinado no login, exigir token nas rotas de escrita de usuários e permitir editar/apagar só o dono da conta ou um admin; definir role só por admin (playbook T03).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: models/user.py:21; routes/user_routes.py:33, 85-86, 129, 209
Description: User.to_dict() inclui 'password': self.password (o hash MD5). Esse dicionário é devolvido por GET /users/<id>, POST /users, PUT /users/<id> e POST /login.
Impact: Quem chama a API recebe o hash MD5 da senha, que se reverte com tabela pronta (ver AP-06).
Recommendation: Remover password da serialização pública (playbook T05).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: app.py:11, 13, 34; services/notification_service.py:7-10
Description: app.config['SECRET_KEY'] = 'super-secret-key-123' (13), URI do banco fixa (11) e app.run(debug=True, host='0.0.0.0') (34). O serviço de notificação tem email_user 'taskmanager@gmail.com' e email_password = 'senha123' fixos (9-10).
Impact: Segredos vão para o repositório; o modo debug escutando em 0.0.0.0 expõe o depurador Werkzeug para a rede.
Recommendation: Mover para config lida de variáveis de ambiente, com .env.example sem valores reais e debug desligado por padrão (playbook T01).

### [CRITICAL] God Class / God File (AP-04)
File: routes/task_routes.py:1-299; routes/report_routes.py:1-223
Description: task_routes.py junta consultas ORM, validação, regra de atraso, estatísticas e HTTP no mesmo arquivo (299 linhas). report_routes.py junta dois domínios (relatórios e CRUD de categorias) com consultas, agregações e HTTP.
Impact: Qualquer mudança de regra mexe na camada HTTP; nada se testa isolado.
Recommendation: Separar em routes (só HTTP), controllers e models, com categorias em arquivo próprio (playbook T04).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: models/user.py:29, 32; routes/user_routes.py:64, 115; seed.py:19, 26, 33
Description: set_password usa hashlib.md5(pwd.encode()).hexdigest() sem salt e check_password compara com ==. Mínimo de 4 caracteres; o seed usa '1234', 'abcd', 'pass'.
Impact: Se o banco ou uma resposta vazar, as senhas se recuperam por tabela MD5 em segundos.
Recommendation: Usar hash com salt e custo (werkzeug.security generate_password_hash/check_password_hash) e comparação em tempo constante (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: routes/task_routes.py:12-63, 86-154, 157-223, 274-299; routes/user_routes.py:43-90, 93-132, 154-183; routes/report_routes.py:13-101, 104-155; services/notification_service.py:4; models/task.py:38-60
Description: Handlers com 30 a 90 linhas que consultam o ORM, validam, calculam atraso e estatísticas e montam a resposta. Os métodos de domínio do model (validate_status, validate_priority, is_overdue) e o NotificationService existem mas as rotas não os usam.
Impact: Regra repetida entre rotas; impossível testar sem HTTP.
Recommendation: Levar regra para controllers/services e acesso a dados para os models; rotas só recebem e respondem (playbook T07).

### [HIGH] Várias gravações sem transação (AP-09)
File: seed.py:11-14, 37, 63, 92
Description: O seed apaga as três tabelas e faz commit (14), depois grava usuários, categorias e tasks em três commits separados (37, 63, 92).
Impact: Uma falha no meio deixa o banco vazio ou com usuários sem tasks. O efeito fica restrito ao script de carga.
Recommendation: Fazer o seed numa transação só, usando flush para obter ids (playbook T09).

### [MEDIUM] Consultas N+1 (AP-10)
File: routes/task_routes.py:42, 51; routes/user_routes.py:22; routes/report_routes.py:56, 163
Description: GET /tasks faz User.query.get e Category.query.get por task; GET /users carrega u.tasks (lazy) por usuário; /reports/summary faz Task.query.filter_by(user_id=u.id) por usuário; GET /categories faz um count por categoria.
Impact: O número de consultas cresce com o número de linhas.
Recommendation: Usar joinedload/selectinload ou agregar com GROUP BY (playbook T10).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: routes/task_routes.py:113, 167-169, 182, 261, 264; routes/user_routes.py:103, 115, 125; routes/report_routes.py:196-198, 180, 202
Description: PUT /categories/<id> usa data = request.get_json() sem tratar None ('name' in None → 500). priority é comparada com int sem checar o tipo (priority "alta" → TypeError → 500). len(data['title']) e len(data['password']) quebram com null. int(priority)/int(user_id) em /tasks/search sem tratar erro. name e active do usuário, nome e color da categoria são gravados sem validação (is_valid_color existe e não é usado).
Impact: Erro 500 onde deveria ser 400; dados inválidos no banco.
Recommendation: Centralizar validadores reutilizados por criação e atualização (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: routes/task_routes.py:62, 137, 151-154, 204, 221, 236; routes/user_routes.py:87-90, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 48, 88; app.py:1-34
Description: except: sem tipo em vários handlers, except Exception as e que só imprime e devolve mensagem genérica, e nenhum @app.errorhandler na aplicação: o que não é capturado vira página de debug do Werkzeug.
Impact: Falhas reais ficam escondidas ou expõem o traceback; respostas de erro sem padrão.
Recommendation: Exceções de domínio e handler de erro central (playbook T11).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: routes/task_routes.py:275-287; routes/report_routes.py:15-43, 56-61, 109-135
Description: /tasks/stats faz cinco COUNT separados e carrega todas as tasks para contar atrasadas em Python; /reports/summary faz nove COUNT separados e carrega todas as tasks; contagens por usuário e por status são feitas em laço Python.
Impact: Memória e tempo crescem com a tabela.
Recommendation: Agregar no banco com GROUP BY e filtros (playbook T10).

### [MEDIUM] Código duplicado (AP-14)
File: routes/task_routes.py:17-28, 30-39, 71-80, 96-114, 166-184, 284-287; routes/user_routes.py:61, 106, 162-180; routes/report_routes.py:34-36, 67, 132-135, 151; models/task.py:23-36, 50-60; utils/helpers.py:14-17, 21, 57-108
Description: A regra "está atrasada" aparece seis vezes nas rotas e uma no model; a serialização da task está repetida à mão; validação de título/status/prioridade duplicada entre criação e atualização e de novo em helpers.process_task_data; regex de e-mail em três lugares; cálculo de completion_rate repetido.
Impact: Uma correção feita num lugar e esquecida nos outros.
Recommendation: Concentrar regra no model/controller e reaproveitar (playbook T04 / T07).

### [MEDIUM] Uso de API deprecated (AP-15)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213
Description: Model.query.get(id), API legada no SQLAlchemy 2.0.58 instalado (gera LegacyAPIWarning). datetime.utcnow() não entra: só é deprecated a partir do Python 3.12, e o ambiente usa 3.10.
Impact: Quebra numa próxima versão do SQLAlchemy.
Recommendation: Trocar por db.session.get(Model, id) (playbook T12).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: routes/task_routes.py:96, 99, 110, 113, 167, 169, 177, 182; routes/user_routes.py:64, 71, 115, 120; routes/report_routes.py:45, 129, 180; models/task.py:39; utils/helpers.py:110-116
Description: Lista de status e de roles repetida, limites 3/200 do título, prioridade 1-5, senha mínima 4, janela de 7 dias, "alta prioridade" <= 2 e cor '#000000' soltos no código. As constantes em helpers.py:110-116 existem e ninguém as usa.
Impact: Mudar uma regra exige caçar todas as cópias.
Recommendation: Constantes de domínio num módulo único (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: routes/report_routes.py:10, 24-28, 157-223; routes/task_routes.py:16, 51; routes/user_routes.py:14; models/category.py:14; utils/helpers.py:83
Description: p1..p5 para contagem por prioridade, t, u, c, cat, d, p; o blueprint report_bp e o arquivo report_routes.py hospedam o CRUD de categorias.
Impact: Leitura mais lenta; o nome do arquivo engana sobre o conteúdo.
Recommendation: Renomear variáveis e mover categorias para módulo próprio (playbook T13).

### [LOW] print no lugar de logging (AP-18)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Description: Eventos e erros registrados com print(...).
Impact: Sem nível, sem destino configurável.
Recommendation: Usar logging com logger por módulo (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3, 38-60; models/user.py:34-38; utils/helpers.py:3-7, 9-116; services/notification_service.py:1-48; requirements.txt:4-6
Description: import os, sys, json (app.py), json, os, sys, time (task_routes), hashlib, json (user_routes), format_date, calculate_percentage e json (report_routes), json (models/task), os, json, sys, math, hashlib (helpers) sem uso. Todas as funções e constantes de helpers.py, NotificationService, Task.validate_*/is_overdue e User.is_admin nunca são chamados. marshmallow, requests e python-dotenv nunca são importados.
Impact: Ruído e dependências desnecessárias.
Recommendation: Remover o que não é usado ou passar a usá-lo na refatoração (playbook T13).

================================
Total: 17 findings
================================
```
