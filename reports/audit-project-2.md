```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4.22.1
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: src/AppManager.js:28, 40, 66-75, 80, 131-133
Description: Nenhuma rota verifica quem está chamando. GET /api/admin/financial-report (linha 80) devolve faturamento e nomes de alunos para qualquer pessoa. DELETE /api/users/:id (linha 131) apaga qualquer conta pelo id. POST /api/checkout, quando o `eml` já existe (linhas 40 e 73-74), ignora `pwd` e matricula e cobra em nome dessa conta. O projeto não tem login nem token.
Impact: Qualquer pessoa lê dados financeiros, apaga usuários e faz compras em nome de contas de outras pessoas.
Recommendation: Token de admin vindo do ambiente para a rota admin e para o DELETE (projeto sem login), e no checkout conferir a senha quando a conta já existe (playbook T03).

### [CRITICAL] God Class / God File (AP-04)
File: src/AppManager.js:4-139
Description: A classe `AppManager` abre a conexão (linha 7), cria as tabelas e faz o seed (`initDb`, linhas 10-23), registra todas as rotas HTTP (`setupRoutes`, linhas 25-138) e contém a regra de pagamento (linha 46) e o relatório financeiro (linhas 80-129).
Impact: Qualquer mudança mexe em banco, regra e HTTP ao mesmo tempo. Nada pode ser testado isoladamente.
Recommendation: Separar em config, models, services/controllers e routes (playbook T04).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: src/utils.js:1-7
Description: O objeto `config` traz `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_l..."` (prefixo de chave live), `smtpUser` e `port: 3000` fixos no código.
Impact: Segredos de produção ficam no repositório e em toda cópia do código. Não dá para trocar a configuração por ambiente.
Recommendation: Ler a configuração de variáveis de ambiente, com `.env.example` sem valores reais (playbook T01).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave do gateway no log a cada checkout.
Impact: Quem tem acesso aos logs fica com números de cartão e com a chave do gateway de pagamento.
Recommendation: Remover o log ou registrar só os 4 últimos dígitos, nunca a chave (playbook T05).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: src/utils.js:17-23; src/AppManager.js:18, 68
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e corta em 10 (`Buffer.from(pwd).toString('base64').substring(0, 2)`). Com isso, senhas com o mesmo prefixo dão o mesmo "hash", e o valor é reversível. O seed grava a senha '123' em texto puro (linha 18). Sem `pwd`, a senha vira "123456" (linha 68).
Impact: Se o banco vazar, as senhas vazam junto. Senhas diferentes colidem, e as contas criadas sem senha usam uma senha conhecida.
Recommendation: Usar hash com salt (crypto.scrypt) e exigir senha ao criar a conta (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: src/AppManager.js:28-78, 80-129
Description: O handler de checkout tem 50 linhas com validação, 5 consultas SQL, a regra de aprovação do cartão (`cc.startsWith("4")`, linha 46), criação de usuário e auditoria. O handler do relatório faz as consultas e o cálculo da receita dentro da rota.
Impact: A regra não pode ser testada sem HTTP, e trocar o gateway ou o banco obriga a mexer nas rotas.
Recommendation: Rotas só recebem e respondem; controller/service coordena; SQL nos models (playbook T07).

### [HIGH] Várias gravações sem transação (AP-09)
File: src/AppManager.js:50-61, 69-71, 133
Description: O checkout grava usuário (69), matrícula (50), pagamento (54) e auditoria (57) em callbacks aninhados, sem BEGIN/COMMIT/ROLLBACK. Se o pagamento falhar, a matrícula fica. O DELETE de usuário (133) apaga só a linha de `users` e deixa matrículas e pagamentos órfãos; a própria resposta admite isso ("as matrículas e pagamentos ficaram sujos no banco").
Impact: Dados inconsistentes, como matrícula sem pagamento, usuário criado com pagamento recusado ou pagamento de usuário inexistente.
Recommendation: Agrupar as gravações numa transação, com ROLLBACK em caso de erro e remoção em cascata no DELETE (playbook T09).

### [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-10, 12-15; src/AppManager.js:7, 59
Description: `let globalCache = {}` e `let totalRevenue = 0` são variáveis do módulo exportadas. `logAndCache` altera `globalCache` a cada checkout (AppManager.js:59). A conexão é criada no construtor de `AppManager` e usada por todos os handlers via `this.db`.
Impact: O cache cresce sem limite e é compartilhado entre requisições. Não dá para trocar a conexão por outra nos testes.
Recommendation: Remover o cache global e injetar a conexão (playbook T08).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: src/AppManager.js:38, 57, 92-93, 104, 106, 133; src/app.js:1-14
Description: O `err` é ignorado na auditoria (57), nas consultas do relatório (92, 104, 106) e no DELETE (133). Na linha 93, `enrollments.length` é lido sem checar `err`, o que derruba o processo se a consulta falhar. A linha 38 junta erro de banco com "não encontrado" (404). Não existe middleware de erro `(err, req, res, next)`.
Impact: Falhas passam em silêncio, erro de banco vira 404 e uma exceção dentro de um callback derruba o servidor.
Recommendation: Propagar erros para um middleware central com respostas padronizadas (playbook T11).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: src/AppManager.js:29-35, 46, 132
Description: Só é checado se `usr`, `eml`, `c_id` e `card` existem. Não há checagem de tipo: com `card` numérico, `cc.startsWith` lança um TypeError dentro de um callback do sqlite e derruba o processo. Formato do e-mail, `c_id` e o `:id` do DELETE não são validados, e o DELETE responde 200 mesmo para id inexistente.
Impact: Um único corpo inválido derruba a API para todos. Dados inválidos entram no banco.
Recommendation: Validar tipos e formatos na entrada e responder 400 ou 404 (playbook T11).

### [MEDIUM] Consultas N+1 (AP-10)
File: src/AppManager.js:89-106
Description: Para cada curso, `db.all` busca as matrículas (92); para cada matrícula, `db.get` busca o usuário (104) e o pagamento (106).
Impact: O número de consultas cresce com cursos × matrículas × 2, e o relatório fica lento com a base real.
Recommendation: Uma consulta com JOIN entre courses, enrollments, users e payments (playbook T10).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: src/AppManager.js:108-110
Description: A receita por curso é somada em JS (`courseData.revenue += payment.amount` quando `status === 'PAID'`) depois de trazer linha a linha.
Impact: Memória e tempo crescem com a tabela de pagamentos.
Recommendation: Calcular com `SUM(CASE WHEN status='PAID' ...)` no SQL (playbook T10).

### [MEDIUM] Código duplicado (AP-14)
File: src/AppManager.js:96-98, 119-121
Description: O bloco de fechamento `report.push(courseData); coursesPending--; if (coursesPending === 0) res.json(report);` está repetido nos dois ramos do contador manual de callbacks.
Impact: Mudar a forma de terminar o relatório num ramo e esquecer o outro deixa a resposta sem enviar ou enviada duas vezes.
Recommendation: Substituir a contagem manual por uma consulta única ou por async/await (playbook T04 / T07).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: src/AppManager.js:21, 46, 68, 108; src/utils.js:19, 22
Description: A regra "cartão começa com '4' é aprovado" (46), os status 'PAID'/'DENIED' como strings soltas (21, 46, 108), a senha padrão "123456" (68) e os números 10000 e 10 de `badCrypto` aparecem sem constante nomeada.
Impact: Mudar a regra de aprovação ou os status exige procurar strings espalhadas pelo código.
Recommendation: Constantes nomeadas num único módulo (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: src/AppManager.js:4, 29-33, 89, 102; src/utils.js:12, 17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc` (29-33), `c` (89) e `enr` (102), e nomes como `AppManager`, `badCrypto` e `logAndCache`, que não dizem o que fazem. Os nomes de campo `usr`, `eml`, `pwd`, `c_id` e `card` são contrato da API e ficam.
Impact: O código fica difícil de ler e de revisar.
Recommendation: Renomear para nomes de domínio, mantendo o contrato do corpo (playbook T13).

### [LOW] `print` / `console.log` no lugar de logging (AP-18)
File: src/AppManager.js:45; src/utils.js:13; src/app.js:13
Description: Eventos e "cache" registrados com `console.log`, sem nível nem destino configurável.
Impact: Não dá para filtrar por nível nem desligar o log em produção.
Recommendation: Um logger central com níveis (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: src/AppManager.js:2; src/utils.js:2-3, 5, 10, 25
Description: `totalRevenue` é importado em AppManager.js:2 e nunca usado; `totalRevenue` e `globalCache` são exportados e nunca lidos; `dbUser`, `dbPass` e `smtpUser` não são usados em lugar nenhum.
Impact: Ruído, e segredos que ficam no código sem nem ter uso.
Recommendation: Remover (playbook T13).

Deprecated APIs: none detected
================================
Total: 17 findings
================================
```
