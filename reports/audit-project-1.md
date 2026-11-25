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
File: models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 291, 293, 295, 297; app.py:69
Description: Todas as queries de models.py são montadas por concatenação, ex.: "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" (models.py:110). Texto livre do corpo (nome, descricao, categoria, email, senha, status) e da query string (q, categoria em /produtos/busca, models.py:291, 293) chega direto ao SQL. app.py:69 executa o SQL recebido no corpo (dados["sql"]).
Impact: Um e-mail ' OR '1'='1' -- faz login sem senha; nomes de produto, status ou termos de busca permitem ler/alterar qualquer tabela; /admin/query dá controle total do banco.
Recommendation: Consultas parametrizadas com placeholders ? em todos os pontos; restringir /admin/query (playbook T02, T03).

### [CRITICAL] Endpoint sensível sem autenticação (AP-03)
File: app.py:47-57, 59-78, 14, 15, 16, 23, 26; controllers.py:167-186, 195, 237-245
Description: POST /admin/reset-db apaga as 4 tabelas e POST /admin/query executa SQL arbitrário, sem nenhuma checagem. POST/PUT/DELETE /produtos alteram o catálogo e preços sem exigir admin. POST /pedidos grava em nome do usuario_id que vier no corpo (controllers.py:195). PUT /pedidos/<id>/status altera o pedido de qualquer pessoa. O login (controllers.py:167-186) não devolve token nem cria sessão, então nenhuma rota tem como saber quem chama.
Impact: Qualquer pessoa apaga o banco, roda SQL, muda preços, cria pedidos em nome de outros e aprova/cancela pedidos alheios.
Recommendation: Login devolvendo token assinado; decorator de autenticação/autorização (admin para /admin/* e escrita de /produtos; dono ou admin para pedidos) (playbook T03).

### [CRITICAL] Dado sensível exposto em resposta ou log (AP-05)
File: models.py:83, 99; controllers.py:285-289; controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292; app.py:78; controllers.py:161, 179, 182
Description: O serializador de usuário inclui "senha" (models.py:83, 99): GET /usuarios e GET /usuarios/<id> devolvem as senhas. GET /health devolve "secret_key": "minha-chave-super-secreta-123", "debug": True e "db_path" (controllers.py:286-289). Todos os handlers devolvem str(e) ao cliente. E-mails são impressos no log em cadastro e login.
Impact: Vazamento de senhas, da chave de assinatura e de detalhes internos para qualquer cliente e para os logs.
Recommendation: Tirar senha da serialização, tirar config do /health, mensagem de erro genérica com detalhe só no log do servidor (playbook T05).

### [CRITICAL] Credenciais e configuração hardcoded (AP-01)
File: app.py:7, 8, 88; controllers.py:287-289; database.py:5
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123" (app.py:7), DEBUG = True (app.py:8) e app.run(host="0.0.0.0", port=5000, debug=True) (app.py:88) fixos no código; a mesma chave repetida em controllers.py:289; caminho do banco fixo em database.py:5.
Impact: A chave vai para o repositório; o depurador do Werkzeug fica exposto na rede (0.0.0.0 + debug), permitindo execução remota de código.
Recommendation: Centralizar config em módulo lido de variáveis de ambiente, com debug desligado por padrão (playbook T01).

### [CRITICAL] God Class / God File (AP-04)
File: app.py:1-88; models.py:1-314; database.py:7-86
Description: app.py junta configuração, registro de rotas e SQL direto (DELETE em app.py:51-54, execute em app.py:69). models.py (314 linhas) cobre produtos, usuários, pedidos e relatórios, misturando SQL, regra de negócio (desconto em models.py:256-262, checagem de estoque em models.py:144) e formatação. database.py junta conexão, schema e seed.
Impact: Qualquer mudança mexe em vários domínios; nada é testável isoladamente.
Recommendation: Separar em config, models por domínio, controllers, rotas (blueprints) e seed próprio (playbook T04).

### [HIGH] Senha guardada sem hash forte (AP-06)
File: database.py:76-78; models.py:110, 127-128; controllers.py:155, 160
Description: Senhas gravadas e comparadas em texto puro: seed com "admin123", "123456", "senha123" (database.py:76-78); INSERT direto do valor recebido (models.py:127-128); login compara senha = '...' no SQL (models.py:110).
Impact: Se o banco vazar (ou via /admin/query, GET /usuarios), todas as senhas vazam legíveis.
Recommendation: Hash com werkzeug.security.generate_password_hash / check_password_hash (playbook T06).

### [HIGH] Regra de negócio e acesso a dados na rota (AP-07)
File: controllers.py:3, 264-274, 24-62, 208-210, 247-250; app.py:49-55, 66-76; models.py:256-262
Description: controllers.py importa get_db e executa SQL no health_check (controllers.py:266-274); rotas admin de app.py executam SQL direto. criar_produto tem 39 linhas de validação inline. Notificações (e-mail/SMS/push) são efeitos colaterais no controller (controllers.py:208-210, 247-250). Regra de desconto fica no model de dados (models.py:256-262).
Impact: Regras repetidas e impossíveis de testar sem HTTP; trocar o banco exige mexer nas rotas.
Recommendation: SQL só nos models, validação/regras em controllers/services, notificação num service (playbook T07).

### [HIGH] Estado global mutável (AP-08)
File: database.py:4, 8-11
Description: db_connection = None no módulo + global db_connection; uma única sqlite3.connect(..., check_same_thread=False) compartilhada por todas as requisições/threads.
Impact: Requisições simultâneas compartilham cursor/transação; o commit de uma confirma gravações pela metade de outra.
Recommendation: Conexão por requisição em flask.g, fechada no teardown (playbook T08).

### [HIGH] Várias gravações sem transação (AP-09)
File: models.py:139-168
Description: criar_pedido faz INSERT em pedidos, INSERT em itens_pedido e UPDATE de estoque em laço, com um único commit no fim e nenhum rollback; a checagem de estoque (models.py:144) é separada do UPDATE (models.py:163-166).
Impact: Uma exceção no meio deixa gravações pendentes na conexão compartilhada, que o próximo commit (de outra requisição) confirma: pedido sem itens ou estoque baixado sem pedido. Pedidos concorrentes podem deixar estoque negativo.
Recommendation: Bloco transacional com with conn: (commit/rollback automático) (playbook T09).

### [MEDIUM] Consultas N+1 (AP-10)
File: models.py:187-199, 219-231, 139-141, 154-156
Description: Para cada pedido, uma consulta de itens (cursor2) e, para cada item, uma consulta do nome do produto (cursor3). criar_pedido consulta o produto duas vezes por item.
Impact: GET /pedidos faz 1 + P + I consultas; cresce com os dados.
Recommendation: JOIN de itens_pedido com produtos e agrupamento por pedido (playbook T10).

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-11)
File: controllers.py:170, 240, 43-46, 87-90, 196, 119, 121, 153-158; models.py:144
Description: login e atualizar_status usam dados.get sem tratar corpo None (500). preco/estoque não têm tipo conferido ("abc" < 0 vira 500). PUT /produtos não valida tamanho do nome nem categoria, ao contrário do POST. Itens do pedido não são validados: quantidade negativa passa na checagem de estoque (models.py:144) e aumenta o estoque; produto_id ausente dá KeyError 500. float(preco_min) sem tratamento. Cadastro aceita e-mail duplicado.
Impact: Dados inválidos no banco (total negativo, estoque inflado) e 500 onde deveria ser 400.
Recommendation: Validadores únicos por recurso, aplicados em criação e atualização (playbook T11).

### [MEDIUM] Tratamento de erro genérico ou ignorado (AP-12)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Description: Cada handler repete try/except Exception as e: return jsonify({"erro": str(e)}), 500. Não há @app.errorhandler.
Impact: Detalhes internos vazam; erros de cliente viram 500.
Recommendation: Exceções de domínio + error handler central (playbook T11).

### [MEDIUM] Processamento em memória do que o banco faz (AP-13)
File: models.py:239-254; controllers.py:269-274
Description: relatorio_vendas faz 5 consultas separadas (COUNT, SUM e um COUNT por status) que cabem em uma com GROUP BY status; health_check faz 3 COUNT separados.
Impact: Viagens extras ao banco a cada chamada.
Recommendation: Uma consulta agregada (playbook T10).

### [MEDIUM] Código duplicado (AP-14)
File: models.py:12-21, 31-40, 304-313; models.py:79-86, 95-102; models.py:171-201, 203-233; controllers.py:28-46, 72-90
Description: Mapeamento linha → dict de produto repetido 3 vezes e o de usuário 2 vezes; get_pedidos_usuario e get_todos_pedidos são iguais salvo o WHERE; validação de produto copiada entre criar e atualizar.
Impact: Correção feita num lugar e esquecida no outro (já aconteceu: PUT não valida categoria).
Recommendation: Funções de serialização e consulta compartilhadas (playbook T04 / T07).

### [LOW] Magic numbers e strings de domínio soltas (AP-16)
File: models.py:257-262, 247-253; controllers.py:52, 242, 47-50, 285-286
Description: Faixas de desconto 10000/0.1, 5000/0.05, 1000/0.02 no meio do código; lista de categorias e de status como literais; limites 2 e 200 do nome; "1.0.0" e "producao" fixos.
Impact: Regra difícil de achar e de mudar de forma consistente.
Recommendation: Constantes nomeadas num módulo de domínio (playbook T13).

### [LOW] Nomes pouco expressivos (AP-17)
File: models.py:24, 54, 65, 89, 187, 191, 219, 223; controllers.py:14, 56, 64, 98, 136, 160
Description: Parâmetro/variável id esconde o builtin id(); cursor2 e cursor3 numerados.
Impact: Leitura difícil e risco de sombrear o builtin.
Recommendation: Renomear (produto_id, usuario_id, itens_cursor...) (playbook T13).

### [LOW] print no lugar de logging (AP-18)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: Eventos, erros e "envio" de e-mail/SMS/push registrados com print.
Impact: Sem nível nem destino configurável; logs de erro somem.
Recommendation: logging com logger por módulo (playbook T13).

### [LOW] Imports sem uso e código morto (AP-19)
File: models.py:2; database.py:2; controllers.py:268
Description: import sqlite3 em models.py e import os em database.py nunca usados; cursor.execute("SELECT 1") sem leitura do resultado, seguido de outras consultas.
Impact: Ruído e dependências aparentes que não existem.
Recommendation: Remover (playbook T13).

Deprecated APIs: none detected
================================
Total: 18 findings
================================
```
