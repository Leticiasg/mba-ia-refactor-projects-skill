```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 291, 293, 295, 297
Description: Todas as queries de models.py são montadas por concatenação, ex.: "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" (models.py:110). Campos de texto livre do corpo (nome, descricao, categoria, email, senha) e da query string (q, categoria em /produtos/busca, models.py:291, 293) chegam direto ao SQL.
Impact: Um email ' OR '1'='1' -- faz login sem senha; nomes de produto ou termos de busca permitem ler/alterar qualquer tabela.
Recommendation: Trocar por consultas parametrizadas com placeholders ? em todos os pontos (playbook T02).

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: app.py:47-57, 59-78
Description: POST /admin/reset-db executa DELETE em todas as 4 tabelas; POST /admin/query executa qualquer SQL recebido no corpo (cursor.execute(query), app.py:69) e faz commit. Nenhuma checagem de token, sessão ou papel.
Impact: Qualquer pessoa com acesso à porta apaga o banco ou executa SQL arbitrário (inclusive ler todas as senhas).
Recommendation: Proteger as rotas admin com decorator de autenticação/autorização e remover/restringir o endpoint de SQL arbitrário (playbook T03).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: models.py:83, 99; controllers.py:286-289; controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292; app.py:78; controllers.py:161, 179, 182
Description: O serializador de usuário inclui "senha" (models.py:83, 99), então GET /usuarios e GET /usuarios/<id> devolvem todas as senhas. GET /health devolve "secret_key": "minha-chave-super-secreta-123", "debug": True e "db_path" (controllers.py:286-289). Todos os handlers devolvem str(e) ao cliente. E-mails são impressos em log no cadastro/login.
Impact: Vazamento de senhas, da chave de assinatura de sessão e de detalhes internos para qualquer cliente e para os logs.
Recommendation: Remover senha da serialização, tirar config do /health, devolver mensagens de erro genéricas e logar o detalhe no servidor (playbook T05).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: app.py:7, 8, 88; controllers.py:287-289; database.py:5
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123" (app.py:7), DEBUG = True (app.py:8), app.run(host="0.0.0.0", port=5000, debug=True) (app.py:88); a chave e o debug são repetidos no /health; caminho do banco "loja.db" fixo.
Impact: A chave vai para o repositório e para qualquer cópia; o debugger do Werkzeug fica exposto em 0.0.0.0, permitindo execução remota de código.
Recommendation: Centralizar config num módulo de settings lendo variáveis de ambiente com defaults seguros; debug desligado por padrão (playbook T01).

### [CRITICAL] God Class / God File (AP-04)
File: controllers.py:1-292; app.py:1-88; models.py:1-314; database.py:1-86
Description: controllers.py junta HTTP (request/jsonify), validação, regra de negócio (notificações 208-210, 247-250) e SQL direto (health_check 266-274 via get_db). app.py junta config, registro de rotas e SQL (47-78). models.py (314 linhas) cobre 4 domínios (produtos, usuários, pedidos, relatórios) e contém a regra de desconto (256-262). database.py junta conexão, schema e seed.
Impact: Qualquer mudança mexe em várias camadas; nada se testa isolado.
Recommendation: Separar em config / models por domínio / controllers / rotas (Blueprints) / services (playbook T04).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: database.py:76-78; models.py:126-128, 110
Description: Seed grava senhas em texto puro ("admin123", "123456", "senha123"); criar_usuario grava o valor recebido; login compara a senha pura dentro do SQL.
Impact: Se o banco vazar, todas as senhas vazam junto (e /usuarios já as expõe).
Recommendation: Usar werkzeug.security.generate_password_hash / check_password_hash (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: controllers.py:3, 264-274; controllers.py:24-62, 188-220, 237-255; app.py:47-78
Description: O controller importa a conexão (from database import get_db) e executa SQL no health_check; criar_produto tem 39 linhas com toda a validação e a lista de categorias; criar_pedido e atualizar_status_pedido disparam "notificações" (email/SMS/push) dentro do handler; rotas /admin executam SQL em app.py.
Impact: Regras não reutilizáveis nem testáveis sem HTTP; trocar o banco exige mexer nas rotas.
Recommendation: Mover validação/regras para service/controller, notificações para um service e SQL para os models (playbook T07).

### [HIGH] Estado global mutável (AP-08)
File: database.py:4, 8-11
Description: db_connection = None no módulo + global db_connection + sqlite3.connect(..., check_same_thread=False): uma única conexão compartilhada entre todas as requisições/threads.
Impact: Requisições simultâneas compartilham cursor e transação; um commit de uma requisição pode persistir gravações pela metade de outra.
Recommendation: Conexão por requisição (flask.g + teardown_appcontext) (playbook T08).

### [HIGH] Várias gravações sem transação (AP-09)
File: models.py:139-168
Description: criar_pedido verifica estoque (144), insere o pedido (148-151) e depois, em laço, insere itens e baixa estoque (157-166) com um único commit no fim e sem rollback; a baixa de estoque não revalida disponibilidade (estoque - n sem WHERE estoque >= n).
Impact: Uma exceção no meio do laço deixa gravações pendentes na conexão compartilhada, que o próximo commit de qualquer requisição persiste (pedido sem itens, estoque baixado); pedidos concorrentes podem deixar estoque negativo.
Recommendation: Envolver em transação (with conn: / BEGIN + ROLLBACK em erro) (playbook T09).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: controllers.py:169-170, 239-240; app.py:61-62; controllers.py:43-46, 81-90; controllers.py:118-121; controllers.py:195-201 + models.py:140, 144; controllers.py:245
Description: request.get_json() sem tratar None em login, atualizar_status e admin/query (corpo vazio → 500); preco/estoque sem checagem de tipo ("abc" < 0 → TypeError → 500); atualização não valida tamanho do nome nem categoria, ao contrário da criação; float(preco_min) sem tratamento; itens do pedido não validados (falta de produto_id → KeyError; quantidade 0/negativa aceita); atualizar status de pedido inexistente devolve 200.
Impact: Dados inválidos no banco e 500 onde deveria ser 400/404.
Recommendation: Validação centralizada por recurso, 400/404 consistentes, mesma validação em criar e atualizar (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Description: Todos os handlers repetem try/except Exception as e: return jsonify({"erro": str(e)}), 500; não existe @app.errorhandler.
Impact: Detalhes internos vazam (ver AP-05), código repetido 17 vezes, erros esperados e bugs ficam indistinguíveis.
Recommendation: Exceções de domínio + error handlers centralizados (playbook T11).

### [MEDIUM] Consultas N+1 (AP-10)
File: models.py:187-193, 219-225; models.py:139-140, 154-155
Description: Para cada pedido, uma query de itens (cursor2), e para cada item, uma query do nome do produto (cursor3); criar_pedido consulta cada produto duas vezes em dois laços.
Impact: Número de queries cresce com pedidos × itens; GET /pedidos fica lento.
Recommendation: JOIN entre itens_pedido e produtos / IN (...) e buscar os produtos uma só vez (playbook T10).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: models.py:239-254; controllers.py:269-274
Description: Relatório faz 5 queries separadas (COUNT, SUM e três COUNT por status) que cabem numa única query com agregação condicional; health_check faz mais 3 COUNTs.
Impact: Round-trips extras a cada chamada.
Recommendation: Uma query com SUM(CASE WHEN status = ? ...) / GROUP BY (playbook T10).

### [MEDIUM] Código duplicado (AP-14)
File: models.py:12-21, 31-40, 304-313; models.py:79-86, 95-102; models.py:171-201 vs 203-233; controllers.py:28-46 vs 72-90
Description: Mapeamento linha→dict de produto repetido 3 vezes e de usuário 2 vezes; get_pedidos_usuario e get_todos_pedidos são idênticos exceto pelo WHERE; validação de criar/atualizar produto copiada.
Impact: Correção feita num lugar e esquecida no outro (a atualização já perdeu parte da validação).
Recommendation: Helpers row_to_dict por entidade, uma função de listagem de pedidos com filtro opcional, validador compartilhado (playbook T04 / T07).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: models.py:257-262; controllers.py:47-50, 52, 242; models.py:150, 247-253; app.py:36; controllers.py:285-286
Description: Faixas de desconto 10000/0.1, 5000/0.05, 1000/0.02; limites de nome 2/200; listas de categorias e status inline; strings 'pendente', 'aprovado', 'cancelado' espalhadas; versão "1.0.0" duplicada.
Impact: Regras de negócio escondidas e divergentes quando mudam.
Recommendation: Constantes nomeadas num módulo de domínio (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: controllers.py:14, 56, 64, 98, 136, 160; models.py:24, 54, 65, 89; models.py:187, 191, 219, 223
Description: Parâmetro/variável id esconde o builtin; cursor2, cursor3 numerados.
Impact: Leitura mais difícil e risco de bugs sutis.
Recommendation: Renomear para produto_id / usuario_id / itens_cursor etc. (playbook T13).

### [LOW] print no lugar de logging (AP-18)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: Eventos, erros e "envio" de email/SMS/push registrados com print().
Impact: Sem níveis nem destino configurável.
Recommendation: Módulo logging com logger por módulo (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: models.py:2; database.py:2; controllers.py:268
Description: import sqlite3 em models.py e import os em database.py nunca usados; cursor.execute("SELECT 1") no health_check com resultado descartado.
Impact: Ruído e dependências falsas.
Recommendation: Remover (playbook T13).

Deprecated APIs: none detected
================================
Total: 18 findings
================================
```
