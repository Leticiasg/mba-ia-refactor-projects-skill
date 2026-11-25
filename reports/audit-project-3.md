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
File: routes/task_routes.py:85, 156, 225; routes/user_routes.py:42, 52, 71, 92, 119-125, 134, 210; routes/report_routes.py:167, 190, 211
Description: Nenhuma rota verifica quem chama. O login devolve 'fake-jwt-token-' + str(user.id) (user_routes.py:210), um token previsível que nenhuma rota confere. Qualquer pessoa pode: criar task em nome de qualquer user_id (POST /tasks); alterar ou apagar a task de outro usuário (PUT/DELETE /tasks/<id>); criar uma conta com role "admin" (POST /users aceita role do corpo, linhas 52 e 71); trocar email, senha, role e active de qualquer conta, inclusive a de um admin (PUT /users/<id>); apagar qualquer conta e as tasks dela (DELETE /users/<id>); criar, alterar e apagar categorias, que são de todos (POST/PUT/DELETE /categories).
Impact: Tomada de qualquer conta (troca de senha ou de e-mail), escalada para admin pelo cadastro, e alteração ou exclusão dos dados de outras pessoas.
Recommendation: Emitir um token assinado no login, exigir o token nas rotas que gravam e checar dono ou admin; role e active só por admin; categorias só por admin (playbook T03).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: models/user.py:21; routes/user_routes.py:33, 85, 129, 209
Description: User.to_dict() inclui 'password': self.password (o hash MD5). Essa serialização é devolvida por GET /users/<id>, POST /users, PUT /users/<id> e POST /login.
Impact: Qualquer cliente obtém o hash MD5 sem salt de qualquer usuário e o reverte com tabela pronta (ver AP-06).
Recommendation: Retirar password da serialização pública (playbook T05).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: app.py:11, 13, 34; services/notification_service.py:7-10
Description: SECRET_KEY = 'super-secret-key-123' (app.py:13), URI do banco fixa (app.py:11), app.run(debug=True, host='0.0.0.0') (app.py:34) e credenciais SMTP no código: email_user 'taskmanager@gmail.com', email_password 'senha123' (notification_service.py:9-10).
Impact: Segredos vão para o repositório; o debugger do Werkzeug fica exposto na rede com host 0.0.0.0, o que permite executar código remotamente.
Recommendation: Mover para config lida de variáveis de ambiente, com debug desligado por padrão (playbook T01).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: models/user.py:29, 32; seed.py:19, 26, 33
Description: set_password usa hashlib.md5(pwd.encode()).hexdigest() sem salt; check_password compara com ==. O seed grava senhas fracas ('1234', 'abcd', 'pass'), e o mínimo aceito é 4 caracteres.
Impact: Se o banco ou uma resposta da API vazar (AP-05), as senhas se revertem na hora.
Recommendation: werkzeug.security.generate_password_hash / check_password_hash (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299; routes/user_routes.py:42-90, 92-132, 134-151; routes/report_routes.py:12-101, 103-155; services/notification_service.py:4
Description: Os handlers fazem consultas ORM, validação, cálculo de atraso, estatísticas e montagem de resposta no mesmo corpo (create_task tem 70 linhas, summary_report tem 90). NotificationService existe, mas nenhuma rota a usa.
Impact: Regras repetidas entre rotas (ver AP-14), impossível testar sem HTTP.
Recommendation: Rotas finas → controllers → services/models (playbook T07).

### [HIGH] God Class / God File (AP-04)
File: routes/report_routes.py:12-223
Description: O blueprint de relatórios também concentra o CRUD de categorias (linhas 157-223), num arquivo que junta consultas, regras de estatística e HTTP de dois domínios diferentes.
Impact: Mudanças em categorias e em relatórios se misturam; nenhuma das partes se testa isolada.
Recommendation: Separar categorias em rota/controller próprios (playbook T04).

### [MEDIUM] Consultas N+1 (AP-10)
File: routes/task_routes.py:42, 51; routes/user_routes.py:22; routes/report_routes.py:56, 163
Description: User.query.get e Category.query.get dentro do laço de GET /tasks; len(u.tasks) carrega o relacionamento por usuário; Task.query.filter_by(user_id=u.id) por usuário no summary; .count() por categoria em GET /categories.
Impact: O número de consultas cresce com o número de linhas.
Recommendation: joinedload / GROUP BY (playbook T10).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: routes/task_routes.py:275-287; routes/report_routes.py:15-43, 56-61, 109-135
Description: Quatro COUNT separados por status e cinco por prioridade em vez de um GROUP BY; Task.query.all() percorrido só para contar atrasadas; contagem de concluídas por usuário feita em Python.
Impact: Tempo e memória crescem com a tabela.
Recommendation: Agregar no banco com func.count + group_by e filtrar atrasadas na query (playbook T10).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: routes/task_routes.py:113, 167-169, 182, 261, 264; routes/user_routes.py:103, 115, 125; routes/report_routes.py:180, 196-202
Description: priority comparada sem checar o tipo ("2" < 1 vira TypeError → 500); len(data['title']) quebra com null; int(priority)/int(user_id) na busca sem try (→ 500); name, password e active sem checagem no PUT /users; color sem validação (is_valid_color existe e não é usado); update_category usa data sem tratar None (corpo vazio → 500).
Impact: Erro 500 onde deveria ser 400; dados inválidos no banco.
Recommendation: Validação centralizada, igual no create e no update (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: routes/task_routes.py:62, 137, 204, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88; services/notification_service.py:23; app.py (sem errorhandler)
Description: Vários except: sem tipo, que engolem qualquer erro; nenhum @app.errorhandler; erros de entrada viram 500 sem tratamento.
Impact: Falhas reais ficam escondidas e o cliente recebe respostas inconsistentes.
Recommendation: Exceções de domínio + error handler central (playbook T11).

### [MEDIUM] Código duplicado (AP-14)
File: routes/task_routes.py:17-39, 71-80, 92-114, 166-184, 283-287; routes/user_routes.py:61, 106, 162-180; routes/report_routes.py:34-36, 67, 132-135, 151; models/task.py:38-60; utils/helpers.py:21, 57-108
Description: A regra "está atrasada" aparece 6 vezes, embora Task.is_overdue (models/task.py:50) exista e não seja usado; a serialização de Task é refeita à mão (task_routes.py:17-28, user_routes.py:162-169); a validação de task se repete em create, update e process_task_data (que não é usado); a regex de e-mail aparece 3 vezes; o cálculo de completion_rate aparece 3 vezes, ao lado de calculate_percentage, importado e não usado.
Impact: Uma correção num lugar é esquecida nos outros.
Recommendation: Centralizar em model/serializer/validator únicos (playbook T04 / T07).

### [MEDIUM] Uso de API deprecated (AP-15)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213
Description: Model.query.get(id), API legada no SQLAlchemy 2.0.58 / Flask-SQLAlchemy 3.1.1 instalados (gera LegacyAPIWarning). datetime.utcnow() não entra: ainda não é deprecated no Python 3.10 do .venv.
Impact: Quebra em versões futuras do SQLAlchemy.
Recommendation: db.session.get(Model, id) (playbook T12).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: routes/task_routes.py:96, 99, 104, 110, 113, 167, 169, 177, 182; routes/user_routes.py:64, 71, 115, 120; routes/report_routes.py:45, 129, 180; models/task.py:39, 46; utils/helpers.py:75, 110-116
Description: A lista ['pending','in_progress','done','cancelled'] aparece em 4 lugares, assim como os papéis ['user','admin','manager'], os limites 3/200 do título, a prioridade 1-5, a senha mínima 4, 7 dias e prioridade <= 2. As constantes de utils/helpers.py:110-116 existem e não são usadas.
Impact: Mudar uma regra exige caçar literais em vários arquivos.
Recommendation: Módulo de constantes único (playbook T13).

### [LOW] print no lugar de logging (AP-18)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39, 41
Description: Eventos e erros registrados com print().
Impact: Sem nível nem destino configurável.
Recommendation: Módulo logging (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3, 38-60; models/user.py:34-38; utils/helpers.py:3-7, 9-116; services/notification_service.py:1-48
Description: Imports agrupados e sem uso (os, sys, json, time, hashlib, math); format_date e calculate_percentage importados e não usados; validate_status, validate_priority, is_overdue e is_admin nunca chamados; quase todo utils/helpers.py e todo notification_service.py sem nenhum chamador.
Impact: Ruído; dá a falsa impressão de que existe uma regra centralizada.
Recommendation: Remover ou passar a usar (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: routes/report_routes.py:24-28; routes/user_routes.py:14; routes/task_routes.py:16; models/category.py:14; models/task.py:45
Description: p1..p5, u, t, d e p fora de laços curtos.
Impact: Leitura mais difícil.
Recommendation: Nomes descritivos (playbook T13).

================================
Total: 16 findings
================================
```
