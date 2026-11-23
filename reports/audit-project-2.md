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

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: src/utils.js:1-7; src/AppManager.js:7
Description: O objeto `config` traz segredos fixos no código: dbUser "admin_master", dbPass "senha_super_secreta_prod_123", paymentGatewayKey "pk_l…" (chave com prefixo de produção) e smtpUser. A porta (3000) e o caminho do banco (':memory:') também estão fixos.
Impact: Os segredos vão para o repositório e para qualquer cópia do código. Não dá para trocar de ambiente sem editar o código-fonte.
Recommendation: Ler a configuração de variáveis de ambiente num módulo de config, com defaults seguros, e criar um .env.example sem valores reais (playbook T01).

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: src/AppManager.js:80, 131
Description: GET /api/admin/financial-report devolve a receita e os alunos de cada curso, e DELETE /api/users/:id apaga usuários. Nenhuma das duas verifica token ou sessão.
Impact: Qualquer pessoa lê dados financeiros e pessoais e apaga contas.
Recommendation: Proteger as rotas admin e destrutivas com um middleware de autorização (token de admin vindo da config) (playbook T03).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` escreve no log o número completo do cartão e a chave do gateway de pagamento.
Impact: Quem lê os logs fica com dados de cartão (violação de PCI-DSS) e com a credencial do gateway.
Recommendation: Não logar o cartão nem a chave. No máximo, os 4 últimos dígitos, via logger (playbook T05).

### [CRITICAL] God Class / God File (AP-04)
File: src/AppManager.js:4-139 (initDb 10-23, setupRoutes 25-138)
Description: A classe AppManager abre a conexão (7), cria o schema e o seed (10-23), executa todo o SQL, decide se o pagamento passa (46), monta o relatório e registra as três rotas Express.
Impact: Qualquer mudança mexe na classe inteira, e nada se testa sem subir HTTP e banco juntos.
Recommendation: Separar em config, database, models por entidade, service de checkout/pagamento, controllers e routes (playbook T04).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: src/utils.js:17-23; src/AppManager.js:18, 68
Description: `badCrypto` é base64 dos 2 primeiros caracteres da senha, repetido e truncado em 10 caracteres: não tem salt e é reversível. O seed grava a senha '123' em texto puro (18), e sem `pwd` o código usa a senha padrão "123456" (68).
Impact: Se o banco vazar, as senhas vazam junto. Senhas que começam igual geram o mesmo hash.
Recommendation: Usar hash forte com salt (crypto.scrypt) e exigir senha no cadastro (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: src/AppManager.js:28-78, 80-129, 131-137
Description: O handler de checkout (50 linhas) valida a entrada, consulta curso e usuário, cria o usuário, decide o pagamento (`cc.startsWith("4")`) e grava matrícula, pagamento e auditoria. O handler do relatório faz as consultas e os cálculos dentro da rota.
Impact: A regra de pagamento fica presa ao HTTP, não dá para testá-la isolada e trocar o banco exige reescrever as rotas.
Recommendation: Rotas só encaminham; controllers coordenam; regra no service; SQL nos models (playbook T07).

### [HIGH] Várias gravações sem transação (AP-09)
File: src/AppManager.js:48, 50-61, 69-71, 133-135
Description: O checkout grava usuário → matrícula → pagamento → audit_log em callbacks aninhados, sem BEGIN/COMMIT. Se o pagamento é recusado (48), o usuário criado em 69 fica no banco. No DELETE (133), o usuário é apagado e as matrículas e pagamentos dele ficam órfãos, como a própria resposta admite.
Impact: Matrícula sem pagamento, usuário criado em checkout recusado, pagamentos órfãos no relatório.
Recommendation: Envolver o checkout e a exclusão em transação (BEGIN/COMMIT/ROLLBACK) e apagar as dependências do usuário na mesma transação (playbook T09).

### [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-15, 25; src/AppManager.js:7
Description: `globalCache` (objeto de módulo) é alterado a cada checkout por `logAndCache` e exportado. `totalRevenue` é um `let` global exportado. A conexão é criada no construtor da classe e compartilhada por todos os handlers, sem injeção.
Impact: O cache cresce sem limite e é compartilhado entre requisições. Os testes dependem da ordem e não há como trocar o banco nos testes.
Recommendation: Remover o cache global (ninguém o lê) e injetar a conexão nos models a partir de um módulo de database (playbook T08).

### [MEDIUM] Consultas N+1 (AP-10)
File: src/AppManager.js:89-92, 102-106
Description: Para cada curso roda um SELECT de enrollments. Para cada matrícula roda um SELECT de users e outro de payments.
Impact: São 1 + C + 2·E consultas: a rota fica mais lenta conforme crescem as matrículas.
Recommendation: Uma consulta só com LEFT JOIN courses/enrollments/users/payments (playbook T10).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: src/AppManager.js:83, 108-110
Description: A receita por curso é somada em JS (`courseData.revenue += payment.amount`) depois de trazer as linhas uma a uma.
Impact: Memória e tempo crescem com a tabela de pagamentos.
Recommendation: Calcular no SQL ou numa única passada sobre o resultado do JOIN (playbook T10).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: src/AppManager.js:29-35, 46, 132
Description: Só confere se os campos existem. `card` não tem o tipo conferido: com um número, `cc.startsWith` lança TypeError dentro do callback do sqlite e derruba o processo. Também não há checagem de formato do e-mail nem do tipo de `c_id`, e `:id` do DELETE não é validado.
Impact: O processo cai com um corpo malformado, e dados inválidos entram no banco.
Recommendation: Validar tipos e formatos no controller e responder 400 (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: src/AppManager.js:38, 57, 92-93, 104, 106, 133-135; src/app.js:5-10
Description: Erro de banco vira 404 "Curso não encontrado" (38). O `err` é ignorado em 57, 104, 106 e 133. Em 93, `enrollments.length` é lido sem checar `err`. O DELETE responde sucesso mesmo com id inexistente. Não há middleware de erro `(err, req, res, next)`.
Impact: Falhas passam em silêncio ou derrubam o processo, e o cliente recebe status errado.
Recommendation: Propagar erros via async/await para um middleware de erro central (playbook T11).

### [MEDIUM] Código duplicado (AP-14)
File: src/AppManager.js:95-99, 117-122
Description: O bloco "push no report, decrementa coursesPending, responde se zerou" aparece duas vezes.
Impact: Corrigir a lógica de término num ponto e esquecer o outro gera resposta duplicada ou que nunca sai.
Recommendation: Substituir pela consulta única com JOIN no model, sem contadores manuais (playbook T07).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: src/AppManager.js:21, 46, 68, 108; src/utils.js:19, 22
Description: Os status 'PAID'/'DENIED' aparecem como strings soltas (21, 46, 108). A regra "cartão começa com 4" (46) e a senha padrão "123456" (68) estão no meio do código, assim como 10000 e 10 no hash.
Impact: Mudar um status ou uma regra exige caçar strings pelo código.
Recommendation: Constantes nomeadas (PAYMENT_STATUS, APPROVED_CARD_PREFIX) (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: src/AppManager.js:4, 26, 29-33; src/utils.js:12, 17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc` e `self`; a classe genérica `AppManager`; funções `badCrypto` e `logAndCache`.
Impact: O código fica difícil de ler e de revisar.
Recommendation: Nomes de domínio (name, email, password, courseId, cardNumber; hashPassword) (playbook T13).

### [LOW] `print` / `console.log` no lugar de logging (AP-18)
File: src/AppManager.js:45; src/utils.js:13; src/app.js:13
Description: Eventos registrados com `console.log`, sem níveis e sem destino configurável.
Impact: Não dá para filtrar nem silenciar logs por ambiente.
Recommendation: Logger central com níveis (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: src/AppManager.js:2; src/utils.js:2-3, 5, 9-10, 25
Description: `totalRevenue` é importado e nunca usado (AppManager.js:2) e nunca muda. `config.dbUser`, `dbPass` e `smtpUser` nunca são lidos. `globalCache` é exportado e ninguém lê.
Impact: Ruído e falsa impressão de funcionalidade (cache, SMTP).
Recommendation: Remover o que não é usado (playbook T13).

Deprecated APIs: none detected
================================
Total: 17 findings
================================
```
