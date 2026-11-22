```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] God Class / God File (AP-04)
File: src/AppManager.js:4-139 (conexão 7, schema e seed 10-23, rotas e regra de negócio 25-138)
Description: A classe AppManager abre a conexão com o banco no construtor, cria as tabelas e faz o seed em initDb() e registra todas as rotas HTTP em setupRoutes(app). Dentro dessas rotas estão o SQL, a regra de pagamento e o relatório financeiro.
Impact: Qualquer mudança mexe na mesma classe. Não dá para testar a regra de checkout ou o relatório sem subir HTTP e banco juntos.
Recommendation: Separar em config, database, models, services/controllers e routes (playbook T04).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: src/utils.js:1-7
Description: O objeto config tem segredos fixos no código: dbUser "admin_master", dbPass "senha_super_secreta_prod_123", paymentGatewayKey "pk_l…" (prefixo de chave live), smtpUser e port 3000. Nenhum valor vem de process.env.
Impact: Os segredos vão para o repositório e para qualquer cópia do código. Trocar uma chave exige um novo deploy.
Recommendation: Ler a configuração de variáveis de ambiente, com default só para os valores que não são segredo (playbook T01).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: src/AppManager.js:45
Description: console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`) grava no log o número completo do cartão e a chave do gateway de pagamento.
Impact: Quem lê os logs vê os cartões dos clientes e a chave de produção (violação de PCI-DSS).
Recommendation: Nunca logar o cartão nem a chave. No máximo, os 4 últimos dígitos mascarados (playbook T05).

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: src/AppManager.js:80, 131
Description: GET /api/admin/financial-report devolve a receita e os nomes dos alunos, e DELETE /api/users/:id apaga usuários. Nenhum dos dois verifica token ou sessão.
Impact: Qualquer pessoa lê os dados financeiros e apaga contas de usuários.
Recommendation: Proteger as rotas com um middleware de autenticação/admin (playbook T03).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: src/utils.js:17-23; src/AppManager.js:18, 68
Description: badCrypto() repete os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres. Não usa salt, dá para reverter e senhas diferentes colidem. Sem pwd, a senha vira "123456" por padrão (linha 68). O seed grava a senha '123' em texto puro (linha 18).
Impact: Se o banco vazar, as senhas são recuperadas na hora. Contas criadas sem senha ficam com uma senha conhecida.
Recommendation: Usar crypto.scrypt/bcrypt com salt e não aceitar senha padrão (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: src/AppManager.js:28-78, 80-129, 131-137
Description: O handler de checkout tem 50 linhas: valida os campos, consulta o curso e o usuário, cria o usuário, decide se o pagamento passa (cc.startsWith("4")) e grava matrícula, pagamento e auditoria. O handler do relatório monta a agregação inteira com SQL dentro da rota.
Impact: A regra fica presa ao HTTP, não dá para reaproveitar nem testar, e trocar o banco exige reescrever as rotas.
Recommendation: Rotas finas que chamam controllers/services, com o SQL nos models (playbook T07).

### [HIGH] Várias gravações sem transação (AP-09)
File: src/AppManager.js:50-61, 69-71, 133-135
Description: O checkout grava o usuário, depois enrollments, depois payments e depois audit_logs em callbacks encadeados, sem BEGIN/COMMIT/ROLLBACK. Se o pagamento falhar, a matrícula fica gravada. O DELETE de usuário não remove as matrículas e pagamentos dele, e a própria resposta admite isso ("as matrículas e pagamentos ficaram sujos no banco").
Impact: Dados inconsistentes: matrícula sem pagamento e registros órfãos de usuários apagados.
Recommendation: Agrupar as gravações de cada operação numa transação e apagar os dependentes na mesma transação (playbook T09).

### [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-10, 14, 25; src/AppManager.js:7
Description: globalCache e totalRevenue são variáveis de módulo exportadas, e logAndCache() altera globalCache a cada checkout. A conexão é criada no construtor de AppManager e acessada direto por this.db/self.db, sem injeção.
Impact: Estado compartilhado entre requisições cresce sem limite, testes dependem da ordem e não dá para trocar o banco em teste.
Recommendation: Remover o estado de módulo e injetar a conexão nos models (playbook T08).

### [MEDIUM] Consultas N+1 (AP-10)
File: src/AppManager.js:89-106
Description: Para cada curso (courses.forEach) roda uma consulta de enrollments (linha 92). Para cada matrícula, roda uma consulta em users (104) e outra em payments (106).
Impact: O número de consultas cresce com cursos × matrículas e a rota fica lenta.
Recommendation: Uma consulta com JOIN entre courses, enrollments, users e payments (playbook T10).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: src/AppManager.js:108-110
Description: A receita por curso é somada em JS (courseData.revenue += payment.amount), linha a linha, em vez de usar SUM com filtro de status no SQL.
Impact: Todo o histórico de pagamentos passa pela aplicação só para virar uma soma.
Recommendation: Calcular a receita com SUM(CASE WHEN status='PAID' ...) GROUP BY course (playbook T10).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: src/AppManager.js:38, 57, 92-93, 104, 106, 133-135; src/app.js:5-10
Description: Erro de banco vira 404 "Curso não encontrado" (38). O err da auditoria é ignorado (57). enrollments.length é lido sem checar err, o que derruba o processo se a consulta falhar (92-93). Os callbacks de users e payments ignoram err (104, 106). O DELETE ignora err e sempre responde sucesso (133-135). Não há middleware de erro no Express.
Impact: Falhas passam em silêncio, o cliente recebe status errado e um erro de banco pode derrubar o processo.
Recommendation: Propagar os erros para um middleware central (err, req, res, next) (playbook T11).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: src/AppManager.js:29-35, 132
Description: O checkout só confere se usr, eml, c_id e card existem. Não confere tipo, formato de e-mail nem se o cartão é string (cc.startsWith quebra com número). pwd é opcional. O :id do DELETE não é validado.
Impact: Dados inválidos chegam ao banco, e um card numérico gera 500 em vez de 400.
Recommendation: Validar tipo e formato na entrada e responder 400 (playbook T11).

### [MEDIUM] Código duplicado (AP-14)
File: src/AppManager.js:96-98, 119-121
Description: O bloco "report.push(courseData); coursesPending--; if (coursesPending === 0) res.json(report)" aparece duas vezes no relatório.
Impact: Uma correção em um dos ramos pode ser esquecida no outro.
Recommendation: Substituir pela consulta única do model e pela montagem num só lugar (playbook T04 / T07).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: src/AppManager.js:21, 46, 48, 68, 108; src/utils.js:19, 22
Description: A regra de aprovação "cartão começa com '4'" (46), os status 'PAID'/'DENIED' repetidos (21, 46, 48, 108), a senha padrão "123456" (68) e as constantes 10000 e 10 de badCrypto estão soltos no código.
Impact: Mudar uma regra ou um status exige caçar strings pelo código.
Recommendation: Extrair para constantes nomeadas (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: src/AppManager.js:4, 29-33; src/utils.js:17
Description: Variáveis u, e, p, cid, cc; a classe AppManager não diz o que faz; a função badCrypto.
Impact: Leitura difícil e intenção escondida.
Recommendation: Renomear com nomes do domínio, mantendo os campos do contrato (usr, eml, pwd, c_id, card) (playbook T13).

### [LOW] `print` / `console.log` no lugar de logging (AP-18)
File: src/AppManager.js:45; src/utils.js:13; src/app.js:13
Description: Eventos de pagamento, cache e boot são registrados com console.log, sem níveis.
Impact: Não dá para filtrar nem desligar logs por ambiente.
Recommendation: Usar um logger simples com níveis (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: src/AppManager.js:2; src/utils.js:2-3, 5, 9-10, 25
Description: totalRevenue é importado em AppManager.js:2 e nunca usado, e em utils.js nunca é alterado nem lido. globalCache é exportado e ninguém lê. config.dbUser, config.dbPass e config.smtpUser não são usados em lugar nenhum.
Impact: Ruído que confunde quem lê e mantém segredos sem motivo.
Recommendation: Remover (playbook T13).

Deprecated APIs: none detected
================================
Total: 17 findings
================================
```
