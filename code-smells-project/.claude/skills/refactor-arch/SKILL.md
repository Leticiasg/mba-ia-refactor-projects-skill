---
name: refactor-arch
description: Audita e refatora um projeto backend para o padrão MVC, em qualquer linguagem ou framework. Analisa a stack, gera um relatório de anti-patterns com severidade e arquivo:linha, pede confirmação e só então reestrutura o código e valida que a aplicação sobe e que os endpoints continuam respondendo. Use quando pedirem auditoria de arquitetura, refatoração para MVC ou limpeza de código legado.
disable-model-invocation: true
---

# refactor-arch

Você vai auditar e refatorar o projeto da pasta atual em três fases, nesta ordem. O conhecimento de domínio está em `references/`. Em cada fase, leia os arquivos indicados **antes** de agir, por inteiro.

## Referências

| Arquivo | Conteúdo | Quando ler |
|---|---|---|
| `references/project-analysis.md` | Heurísticas de detecção de stack, banco, rotas e arquitetura; formato da saída da Fase 1 | Início da Fase 1 |
| `references/anti-patterns.md` | Catálogo AP-01 a AP-19, escala de severidade e sinais de detecção | Início da Fase 2; de novo no fim da Fase 3 |
| `references/report-template.md` | Formato do relatório, pausa obrigatória e gravação do arquivo | Início da Fase 2 |
| `references/mvc-guidelines.md` | Estrutura alvo, responsabilidades de cada camada e checklist | Início da Fase 3 |
| `references/refactoring-playbook.md` | Transformações T01 a T13 com antes/depois em Python e JavaScript | Início da Fase 3 |

## Scripts

Ficam em `scripts/`, na pasta desta skill (a partir da raiz do projeto: `.claude/skills/refactor-arch/scripts/`). Rode-os da raiz do projeto com `bash`; nas instruções abaixo, `scripts/` abrevia esse caminho e `<tmp>` é a pasta temporária do 3.1. Não é preciso ler o código, só o cabeçalho de uso.

| Script | O que faz | Quando usar |
|---|---|---|
| `wait_for_http.sh <url> [timeout]` | Espera a aplicação responder; sai com 1 se o tempo acabar | Depois de subir a aplicação (3.1 e 3.3) |
| `stop_port.sh <porta> [timeout]` | Para o processo que escuta na porta e confirma que ela ficou livre; sai com 1 se não conseguir | Sempre que for parar a aplicação (3.1 e 3.3), no lugar de `pkill` ou `kill` pelo nome |
| `run_requests.sh <base_url> <arquivo>` | Roda a lista de requisições e imprime `METHOD PATH -> STATUS \| forma da resposta` | Baseline (3.1) e validação (3.3) |
| `compare_results.sh <antes> <depois>` | Compara as duas saídas linha a linha e imprime `<n>/<n> requests match baseline` | Validação (3.3) |

As instruções abaixo citam seções pelo título exato, entre aspas. Para achar uma seção, procure o título no arquivo indicado.

## Regras gerais

1. O projeto é a pasta de onde a skill foi chamada. Não altere nada fora dela, exceto o relatório em `reports/` (Fase 2).
2. **Nenhum arquivo é criado, alterado ou apagado nas Fases 1 e 2.** Só leitura e comandos que não escrevem.
3. Não mexa em `.claude/`, `.git/`, `node_modules/`, ambientes virtuais nem em relatórios antigos de outros projetos.
4. Não altere o git: quem versiona é o usuário. Não rode `git add`, `rm`, `mv`, `restore`, `checkout`, `reset`, `stash`, `commit` nem `push`. Para apagar ou mover um arquivo, use `rm` e `mv` do sistema; o usuário decide o que vai para o stage. Comandos git de leitura (`status`, `diff`, `log`, `rev-parse`) são permitidos.
5. Nunca imprima o conteúdo de arquivos `.env`.
6. Tudo o que você afirmar precisa de evidência no código. Se não souber, diga "não detectado".
7. Nada nesta skill depende de um projeto específico. Descubra nomes de arquivos, rotas e comandos a cada execução.

---

## Fase 1 — Análise

Leia `references/project-analysis.md`.

1. Liste os arquivos-fonte, ignorando o que a seção "Arquivos a ignorar" de `references/project-analysis.md` manda ignorar. Conte arquivos e linhas.
2. Detecte linguagem, framework e versão, dependências de runtime e banco de dados, sempre a partir do arquivo de dependências e dos imports.
3. Encontre o entry point, a porta, o comando de instalação, o comando para subir e scripts de seed.
4. Monte o inventário de rotas: método, caminho completo (com prefixos), `arquivo:linha` e campos esperados na entrada.
5. Liste as tabelas, deduza o domínio e classifique a arquitetura atual.
6. Imprima o bloco `PHASE 1: PROJECT ANALYSIS` no formato da seção "Saída da Fase 1" de `references/project-analysis.md`, seguido do inventário de rotas.

Siga direto para a Fase 2.

## Fase 2 — Auditoria

Leia `references/anti-patterns.md` e `references/report-template.md`.

1. Leia todos os arquivos-fonte da lista da Fase 1, linha a linha. Não audite por amostragem.
2. Para cada anti-pattern de `references/anti-patterns.md`, procure os sinais de detecção. Anote cada ocorrência com `arquivo:linha` exato. Confira o número da linha no arquivo antes de escrever.
3. Agrupe ocorrências do mesmo anti-pattern num só finding, com todas as linhas.
4. Verifique APIs deprecated (AP-15) contra as versões detectadas na Fase 1.
5. Audite a própria auditoria, como manda a seção "Regras de uso" de `references/anti-patterns.md`: retire falsos positivos e marque como `(possible)` o que tem evidência parcial.
6. Ordene de CRITICAL para LOW e confira se o `Summary` e o `Total` batem com a lista.
7. Imprima o relatório exatamente no formato da seção "Formato" de `references/report-template.md`.
8. Imprima `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e **encerre a sua resposta aqui**. Espere o usuário responder. Não chame nenhuma ferramenta de edição, não rode instalação e não suba a aplicação antes da resposta.

Respostas:
- **"n"** (ou qualquer recusa): diga que nada foi alterado e pare.
- **"y"**: grave o relatório seguindo a seção "Gravação do arquivo" de `references/report-template.md` e informe o caminho. Depois siga para a Fase 3.

## Fase 3 — Refatoração

Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`. Use os exemplos do playbook na linguagem detectada na Fase 1; em outra linguagem, adapte a técnica dos exemplos e avise o usuário no resumo final.

### 3.1 Baseline (antes de mudar o código)

1. Crie uma pasta temporária fora do projeto (`mktemp -d`) para guardar o baseline e os logs. Nada disso vai para dentro do projeto.
2. Instale as dependências com o comando descoberto na Fase 1. Em Python, use um ambiente virtual dentro do projeto (`.venv/`) se ainda não houver um.
3. Garanta um estado inicial limpo dos dados: se o banco é um arquivo, guarde uma cópia e recrie-o; rode o seed se o projeto tiver um.
4. Confira se a porta está livre com `lsof -i :<porta> -sTCP:LISTEN`. Se houver um processo que você não iniciou, mostre ao usuário e pergunte antes de pará-lo. Suba a aplicação original em segundo plano, com a saída indo para um log, e espere com `scripts/wait_for_http.sh <url base> 20`. Leia o começo do log: se houver erro, mostre ao usuário e pare.
5. Monte a lista de requisições a partir do inventário de rotas, num arquivo `<tmp>/requests.tsv`, no formato descrito no cabeçalho de `scripts/run_requests.sh`: use exemplos do projeto (`*.http`, README) quando existirem; para POST/PUT, monte corpos com os campos que o código lê e ids que existem no seed. Inclua pelo menos um caso de erro esperado (id inexistente ou corpo inválido). Ordem: leituras, criações, atualizações, remoções e, por último, rotas destrutivas (reset, delete em massa).
6. Rode `scripts/run_requests.sh <url base> <tmp>/requests.tsv > <tmp>/before.txt`. Se a saída tiver status `000`, a aplicação não respondeu: investigue antes de seguir. Pare a aplicação com `scripts/stop_port.sh <porta>`.

### 3.2 Refatoração

1. Defina a estrutura alvo pela seção "Estrutura alvo" de `references/mvc-guidelines.md`. Em projeto já organizado, siga a seção "Projeto já parcialmente organizado" do mesmo arquivo (mapear o que existe e ajustar, sem reescrever do zero).
2. Para cada finding do relatório, aplique a transformação indicada em `Recommendation` (Txx), na ordem sugerida no topo de `references/refactoring-playbook.md`.
3. Preserve o contrato da API e o comando para rodar (seção "Princípios" de `references/mvc-guidelines.md`).
4. Atualize os scripts que importam módulos movidos (seed, testes) e o arquivo de dependências, se algo mudar.
5. Anote cada exceção de segurança que muda uma resposta (ex.: campo `senha` removido, rota admin exigindo token).

### 3.3 Validação

1. Volte os dados ao mesmo estado inicial do baseline: apague o banco criado no 3.1 (banco em memória recomeça sozinho ao reiniciar).
2. Se o projeto tem seed, rode-o com o código novo. Ele precisa terminar sem erro.
3. Suba a aplicação refatorada pelo **mesmo comando** da Fase 1 e espere com `scripts/wait_for_http.sh`. Leia o começo do log: erro de import ou de boot é falha.
4. Rode `scripts/run_requests.sh` com o mesmo `<tmp>/requests.tsv`, gravando em `<tmp>/after.txt`, e depois `scripts/compare_results.sh <tmp>/before.txt <tmp>/after.txt`. Cada linha `DIFF` só é aceita se estiver na lista de exceções de segurança. Para conferir uma exceção (ex.: rota que agora exige token), acrescente a requisição com o header num arquivo à parte e rode de novo.
5. Se algo falhar, pare a aplicação com `scripts/stop_port.sh <porta>`, corrija o código e repita a partir do passo 1. Nunca suba uma versão nova sem antes confirmar que a porta ficou livre, ou a versão antiga continua respondendo no lugar dela. Faça no máximo 5 ciclos; se ainda falhar, pare e mostre ao usuário o que quebrou.
6. Pare a aplicação com `scripts/stop_port.sh <porta>` e apague o banco criado na validação, se ele não existia antes. Restaure a cópia guardada no 3.1, se havia uma.
7. Releia o código novo contra `references/anti-patterns.md` e liste o que ainda restar. Não declare "zero anti-patterns" sem ter conferido.

### 3.4 Saída da Fase 3

Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios do projeto refatorado, sem .venv, node_modules e .claude>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly (<n>/<n> requests match baseline, linha final de compare_results.sh)
  ✓ Zero anti-patterns remaining

## Security exceptions
<cada mudança de resposta aceita e o motivo, ou "none">

## Validation log
<método rota → status antes | status depois, uma linha por requisição>
================================
```

Use `✗` em qualquer item que não passou e explique o motivo logo abaixo (ex.: `✗ 2 anti-patterns remaining: AP-16 em ..., AP-17 em ...`). Nunca marque `✓` sem ter rodado a verificação.
