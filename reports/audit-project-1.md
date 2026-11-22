```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299; app.py:62-69
Description: Todas as queries de models.py são montadas por concatenação com dados da requisição, ex.: "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" (models.py:110) e a busca com "nome LIKE '%" + termo + "%'" (models.py:291). Além disso, POST /admin/query executa qualquer SQL recebido no corpo: cursor.execute(query) com query = dados.get("sql") (app.py:62, 69).
Impact: Um email "' OR '1'='1' --" faz login sem senha; o parâmetro q da busca lê qualquer tabela (incluindo senhas); /admin/query permite DROP/UPDATE arbitrário.
Recommendation: Usar placeholders "?" em todas as queries e remover a execução de SQL livre (playbook T02).

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: app.py:47-57, 59-78
Description: POST /admin/reset-db apaga itens_pedido, pedidos, produtos e usuarios (app.py:51-54) e POST /admin/query executa SQL do corpo (app.py:69), ambos sem nenhum decorator ou checagem de token/sessão.
Impact: Qualquer cliente na rede apaga todo o banco ou lê/altera qualquer dado.
Recommendation: Exigir autenticação de admin nessas rotas e eliminar a execução de SQL livre (playbook T03).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: models.py:83, 99; controllers.py:132, 140, 286-289, 12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292; app.py:78; controllers.py:161, 179, 182
Description: A serialização de usuários inclui "senha": row["senha"] (models.py:83, 99), devolvida por GET /usuarios e GET /usuarios/<id> (controllers.py:132, 140). GET /health devolve "db_path", "debug" e "secret_key": "minha-chave-super-secreta-123" (controllers.py:286-289). Todos os handlers devolvem str(e) ao cliente. Logs imprimem e-mail de usuários em criação e login (controllers.py:161, 179, 182).
Impact: Qualquer chamador obtém senhas de todos os usuários e a SECRET_KEY da aplicação; mensagens de exceção revelam estrutura interna do banco.
Recommendation: Remover senha das serializações, tirar config interna do /health e devolver mensagens genéricas em erros 500 (playbook T05).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: app.py:7, 8, 88; controllers.py:286-289; database.py:5, 76-78
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123" (app.py:7), DEBUG = True (app.py:8) e app.run(host="0.0.0.0", port=5000, debug=True) (app.py:88) fixos; o /health repete os valores literais (controllers.py:286-289); caminho do banco fixo "loja.db" (database.py:5); senhas de seed legíveis no código, ex.: ("Admin", "admin@loja.com", "admin123", "admin") (database.py:76).
Impact: A chave vai para o repositório; o depurador Werkzeug fica exposto em 0.0.0.0, permitindo execução de código remoto.
Recommendation: Ler SECRET_KEY, DEBUG, porta e caminho do banco de variáveis de ambiente num módulo de config (playbook T01).

### [HIGH] God Class / God File (AP-04)
File: models.py:1-314; app.py:1-88; database.py:7-86
Description: models.py (314 linhas) cobre quatro domínios (produtos, usuários, pedidos, relatórios) misturando SQL, regra de negócio (checagem de estoque models.py:144-146, faixas de desconto models.py:256-262) e formatação. app.py junta configuração (7-9), registro de rotas (11-30) e handlers com SQL cru (49-55, 66-76). database.py junta conexão, criação de schema e seed (7-86).
Impact: Qualquer mudança em um domínio mexe no mesmo arquivo dos outros; nada é testável isoladamente.
Recommendation: Separar em models/controllers/routes por domínio, config e camada de banco próprias (playbook T04).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: models.py:109-111, 126-129; database.py:76-78
Description: criar_usuario grava a senha recebida em texto puro (models.py:126-129); o login compara senha = '<valor>' direto no SQL (models.py:110); o seed grava "admin123", "123456", "senha123" (database.py:76-78).
Impact: Um vazamento do banco (ou o próprio GET /usuarios) entrega todas as senhas legíveis.
Recommendation: Gerar hash com werkzeug.security.generate_password_hash e verificar com check_password_hash (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: app.py:49-55, 66-76; controllers.py:3, 266-274, 208-210, 247-250
Description: Handlers de app.py executam SQL direto (app.py:51-54, 69). controllers.py importa get_db (controllers.py:3) e faz quatro queries no health_check (266-274). Efeitos colaterais de notificação ("ENVIANDO EMAIL", "ENVIANDO SMS", "ENVIANDO PUSH", controllers.py:208-210; notificações de status 247-250) ficam no handler HTTP.
Impact: Troca de banco ou de canal de notificação exige mexer nas rotas; regras não testáveis sem HTTP.
Recommendation: Mover SQL para models e efeitos colaterais para um serviço chamado pelo controller (playbook T07).

### [HIGH] Estado global mutável (AP-08)
File: database.py:4, 8-11
Description: db_connection = None no módulo, alterado via global db_connection e criado com sqlite3.connect(db_path, check_same_thread=False), compartilhado por todas as requisições e threads.
Impact: Requisições simultâneas usam o mesmo cursor/transação; um commit de uma requisição grava alterações pendentes de outra.
Recommendation: Conexão por requisição (flask.g + teardown_appcontext) (playbook T08).

### [HIGH] Várias gravações sem transação (AP-09)
File: models.py:139-168
Description: criar_pedido insere o pedido (148-151), cada item (157-161) e baixa estoque (163-166) com um único db.commit() no fim (168), sem rollback em caso de exceção. A checagem de estoque (144) é feita antes e separada do UPDATE (164), sem condição atômica.
Impact: Uma exceção no meio deixa INSERTs pendentes na conexão global, que serão confirmados pelo próximo commit de outra requisição (pedido sem itens, estoque baixado sem pedido); dois pedidos simultâneos podem deixar estoque negativo.
Recommendation: Envolver a operação em "with conn:" (commit/rollback) e baixar estoque com WHERE estoque >= ? (playbook T09).

### [MEDIUM] Consultas N+1 (AP-10)
File: models.py:139-141, 154-156, 186-199, 219-231
Description: Em criar_pedido, um SELECT por item (140) e outro SELECT preco repetido por item (155) para o mesmo produto. Em get_pedidos_usuario e get_todos_pedidos, para cada pedido um SELECT em itens_pedido (188, 220) e, para cada item, um SELECT do nome do produto (192, 224) com cursor2/cursor3.
Impact: Listar N pedidos com M itens faz 1 + N + N·M consultas; a rota degrada com o volume.
Recommendation: Usar JOIN entre pedidos, itens_pedido e produtos, e reaproveitar o produto já lido (playbook T10).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: controllers.py:169-170, 239-240, 43-50, 64-91, 118-121, 195-201, 245; app.py:61-62
Description: login e atualizar_status_pedido chamam dados.get(...) sem tratar get_json() == None (controllers.py:170, 240; idem app.py:62); preco/estoque não têm tipo conferido (preco < 0 com string gera TypeError, controllers.py:43); a atualização não valida tamanho do nome nem categoria, que a criação valida (controllers.py:47-54 vs 64-91); float(preco_min) sem tratamento (118-121); itens do pedido sem checar produto_id/quantidade nem quantidade > 0 (195-201); atualizar status de pedido inexistente devolve 200 (245).
Impact: Corpo vazio ou tipo errado vira 500 em vez de 400; quantidade negativa aumenta o estoque; dados inválidos entram via PUT.
Recommendation: Centralizar validação por recurso, reutilizada em criação e atualização, retornando 400 (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Description: Os 16 handlers repetem try/except Exception as e: return jsonify({"erro": str(e)}), 500. Não existe @app.errorhandler.
Impact: Erros de cliente viram 500, detalhes internos vazam e o tratamento não é uniforme.
Recommendation: Handlers de erro centralizados (errorhandler para exceções de domínio e 500 genérico) (playbook T11).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: models.py:239-254
Description: relatorio_vendas faz cinco consultas separadas: COUNT(*), SUM(total) e três COUNT(*) WHERE status = '...'.
Impact: Cinco viagens ao banco onde uma agregação resolve; cresce com novos status.
Recommendation: Uma consulta com COUNT/SUM e SUM(CASE WHEN status = ...) (playbook T10).

### [MEDIUM] Código duplicado (AP-14)
File: models.py:12-21, 31-40, 304-313; models.py:79-86, 95-102; models.py:171-201, 203-233; controllers.py:28-46, 72-90
Description: Mapeamento linha→dict de produto repetido três vezes e de usuário duas vezes; get_pedidos_usuario e get_todos_pedidos são idênticas exceto pelo WHERE; validação de produto copiada entre criar e atualizar.
Impact: Correções aplicadas num lugar e esquecidas no outro (já ocorreu: a atualização não valida categoria).
Recommendation: Funções de mapeamento e validação únicas; uma consulta de pedidos com filtro opcional (playbook T04 / T07).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: models.py:257-262, 150, 247, 250, 253; controllers.py:47-50, 52, 242, 285; app.py:36
Description: Faixas de desconto 10000/0.1, 5000/0.05, 1000/0.02 (models.py:257-262); limites de nome 2 e 200 (controllers.py:47-50); lista de categorias (controllers.py:52) e de status (controllers.py:242) inline; status 'pendente'/'aprovado'/'cancelado' literais no SQL (models.py:150, 247-253); versão "1.0.0" repetida (app.py:36, controllers.py:285).
Impact: Mudar uma regra exige caçar literais espalhados.
Recommendation: Constantes nomeadas num módulo de domínio (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: controllers.py:14, 56, 64, 98, 136, 160; models.py:24, 54, 65, 89, 187, 191, 193, 219, 223, 225
Description: Parâmetro/variável id esconde o builtin (controllers.py:14, 56, ...; models.py:24, 54, 65, 89); cursor2/cursor3 numerados (models.py:187, 191, 219, 223); prod (models.py:193, 225).
Impact: Leitura mais difícil e risco de sombrear o builtin id().
Recommendation: Renomear para produto_id, usuario_id, itens_cursor etc. (playbook T13).

### [LOW] print / console.log no lugar de logging (AP-18)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: Eventos, erros e "envios" de e-mail/SMS/push registrados com print(...).
Impact: Sem níveis nem destino configurável; impossível filtrar em produção.
Recommendation: Usar o módulo logging com logger por módulo (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: database.py:2; models.py:2; controllers.py:268
Description: import os (database.py:2) e import sqlite3 (models.py:2) nunca usados; cursor.execute("SELECT 1") cujo resultado é descartado (controllers.py:268).
Impact: Ruído e dependências aparentes que não existem.
Recommendation: Remover (playbook T13).

Deprecated APIs: none detected
================================
Total: 18 findings
================================
```
