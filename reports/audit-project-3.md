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

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: models/user.py:21; routes/user_routes.py:33, 85, 129, 209
Description: User.to_dict() inclui 'password': self.password (hash MD5). Esse dicionário é devolvido em GET /users/<id>, POST /users, PUT /users/<id> e na resposta de POST /login.
Impact: Qualquer cliente recebe o hash MD5 da senha de qualquer usuário, e esse hash se reverte com tabelas prontas (ver AP-06).
Recommendation: Remover password da serialização pública (playbook T05).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: app.py:11, 13, 34; services/notification_service.py:7-10
Description: SECRET_KEY = 'super-secret-key-123' e a URI do banco fixas no código; app.run(debug=True, host='0.0.0.0'); credenciais SMTP fixas (email_user 'taskmanager@gmail.com', email_password 'senha123').
Impact: Os segredos vão para o repositório. O modo debug aberto em 0.0.0.0 expõe o depurador interativo do Werkzeug para a rede.
Recommendation: Mover para config/settings.py lendo variáveis de ambiente (python-dotenv já está nas dependências) e tirar o debug fixo (playbook T01).

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: routes/user_routes.py:52, 71, 119-122, 134-151, 210
Description: Nenhuma rota verifica identidade. O login devolve 'fake-jwt-token-' + str(user.id), que nada valida. POST /users aceita role 'admin' vinda do corpo, PUT /users/<id> deixa trocar role e active, e DELETE /users/<id> apaga o usuário e todas as tasks dele, tudo sem checagem nenhuma.
Impact: Qualquer pessoa cria um usuário admin, promove contas e apaga usuários com as tasks deles.
Recommendation: Proteger as operações de alteração de privilégio e as destrutivas com um decorator de autenticação/admin (playbook T03).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: models/user.py:29, 32; seed.py:19, 26, 33
Description: set_password usa hashlib.md5(pwd.encode()).hexdigest() sem salt, e check_password compara com ==. O seed grava senhas triviais ('1234', 'abcd', 'pass').
Impact: Se o banco vazar ou os hashes forem expostos (AP-05), as senhas se recuperam na hora.
Recommendation: Usar werkzeug.security generate_password_hash/check_password_hash (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: routes/task_routes.py:12-63, 86-154, 157-223, 274-299; routes/user_routes.py:43-90, 93-132; routes/report_routes.py:13-101, 104-155; services/notification_service.py:4
Description: Os handlers fazem as consultas ao ORM, as validações, a montagem dos DTOs e os cálculos (atraso, taxas de conclusão, relatórios), com corpos de 40 a 90 linhas. A pasta services/ existe, mas nenhuma rota a usa (NotificationService nunca é instanciado).
Impact: Regras repetidas entre rotas, nada se testa sem HTTP, e qualquer mudança de regra mexe na camada web.
Recommendation: Extrair controllers/services e deixar as rotas finas (playbook T07).

### [HIGH] God Class / God File (AP-04)
File: routes/report_routes.py:10, 157-223
Description: O blueprint 'reports' também implementa o CRUD completo de categories (GET/POST/PUT/DELETE /categories), misturando dois domínios num arquivo que ainda junta consulta, cálculo e HTTP.
Impact: Quem procura categorias não as encontra, e mudar relatórios mexe em categorias.
Recommendation: Separar category_routes/category_controller do módulo de relatórios (playbook T04).

### [MEDIUM] Consultas N+1 (AP-10)
File: routes/task_routes.py:42, 51; routes/user_routes.py:22; routes/report_routes.py:56, 163
Description: User.query.get e Category.query.get dentro do laço de GET /tasks; len(u.tasks) com lazy load por usuário; Task.query.filter_by(user_id=u.id) por usuário no summary; count por categoria em GET /categories.
Impact: O número de consultas cresce com o número de linhas, e as listagens ficam lentas.
Recommendation: Usar joins/eager loading ou agregações com GROUP BY (playbook T10).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: routes/report_routes.py:196-197, 180, 202; routes/task_routes.py:113, 167, 182, 261, 264; routes/user_routes.py:102-103, 115, 125
Description: PUT /categories usa 'name' in data sem tratar o corpo nulo (TypeError → 500). priority é comparada com < sem checar o tipo (uma string vira 500). len(data['title']) quebra com None. int(priority) e int(user_id) na busca não tratam ValueError. O PUT de usuário aceita nome vazio e active de qualquer tipo. color não é validada (is_valid_color existe e não é usada).
Impact: Dados inválidos entram no banco, e entradas ruins viram erro 500 em vez de 400.
Recommendation: Centralizar a validação por recurso, igual na criação e na atualização (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: routes/task_routes.py:62, 137, 151, 204, 221, 236; routes/user_routes.py:87, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 48, 88; app.py (sem @app.errorhandler)
Description: Blocos except: nus e except Exception as e repetidos em cada handler, com respostas 500 genéricas montadas à mão; não há nenhum handler de erro central.
Impact: Engole erros de programação (inclusive KeyboardInterrupt/SystemExit), esconde a causa e duplica o código de resposta.
Recommendation: Exceções de domínio e error handler central (playbook T11).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: routes/report_routes.py:19-28, 30-43, 56-61; routes/task_routes.py:276-287
Description: Nove COUNTs separados por status e prioridade (caberiam num GROUP BY); Task.query.all() seguido de laço só para contar atrasadas; todas as tasks de cada usuário carregadas só para contar as 'done'.
Impact: Memória e tempo crescem com a tabela inteira.
Recommendation: Agregar no banco com func.count/GROUP BY e filtro de atraso na query (playbook T10).

### [MEDIUM] Código duplicado (AP-14)
File: routes/task_routes.py:17-28, 30-39, 71-80, 96-100, 110, 167-170, 177, 275-287; routes/user_routes.py:61, 106, 162-180; routes/report_routes.py:15-22, 34-36, 132-135; models/task.py:50-60; utils/helpers.py:21, 57-108
Description: A regra "está atrasada?" está reescrita em 6 lugares, e Task.is_overdue() existe sem uso. A serialização de Task repete to_dict() à mão. Validações de título/status/prioridade e a regex de e-mail aparecem duplicadas entre create/update e em utils. As contagens por status existem em /tasks/stats e em /reports/summary.
Impact: Uma correção feita num lugar fica esquecida nos outros.
Recommendation: Uma única implementação de cada regra no model/service (playbook T04 / T07).

### [MEDIUM] Uso de API deprecated (AP-15)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213
Description: Model.query.get(id) é API legada no SQLAlchemy 2.0.58 instalado (emite LegacyAPIWarning). Observação: datetime.utcnow() (vários arquivos) só é deprecated a partir do Python 3.12; o .venv usa 3.10, então não entra como ocorrência.
Impact: Avisos agora e quebra numa próxima versão maior do SQLAlchemy.
Recommendation: Trocar por db.session.get(Model, id) (playbook T12).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: routes/task_routes.py:96, 99, 110, 113, 167, 169, 177, 182; routes/user_routes.py:64, 71, 115, 120; routes/report_routes.py:45, 129, 180; models/task.py:39, 46; utils/helpers.py:75, 110-116
Description: A lista ['pending','in_progress','done','cancelled'] aparece repetida; os roles também; os limites 3/200 (título), 4 (senha), 1..5 (prioridade), <= 2 (alta prioridade), 7 dias e '#000000' estão soltos no código. As constantes em utils/helpers.py:110-116 existem e não são usadas.
Impact: Mudar uma regra exige caçar todos os literais.
Recommendation: Centralizar em config/constants.py (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: routes/report_routes.py:24-28, 55, 161; routes/task_routes.py:16; models/category.py:14; models/task.py:45; seed.py:16, 39, 78
Description: p1..p5, u, t, c, d, p, td, u1, c1 fora de laços curtos.
Impact: Leitura mais lenta e propensa a erro.
Recommendation: Renomear para nomes de domínio (playbook T13).

### [LOW] print no lugar de logging (AP-18)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39, 41
Description: Eventos e erros registrados com print(), sem nível nem destino configurável.
Impact: Não dá para filtrar nem desligar os logs em produção, e erros se perdem no stdout.
Recommendation: Usar o módulo logging (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3, 38-48; models/user.py:34-38; utils/helpers.py:3-7, 9-116; requirements.txt:4-6
Description: import os, sys, json (app.py), json/os/sys/time (task_routes), hashlib/json (user_routes), format_date/calculate_percentage/json (report_routes) e json (models/task) não são usados. validate_status, validate_priority e is_admin nunca são chamados; quase todo utils/helpers.py está sem uso; marshmallow, requests e python-dotenv não são importados.
Impact: Ruído e falsa impressão de que essas funções estão em uso.
Recommendation: Remover ou passar a usar (playbook T13).

Deprecated APIs: Model.query.get (SQLAlchemy 2.0) — see AP-15
================================
Total: 16 findings
================================
```
