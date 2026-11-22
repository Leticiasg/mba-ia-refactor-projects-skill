---
name: refactor-arch
description: Audita e refatora um projeto backend para o padrão MVC, em qualquer linguagem ou framework. Analisa a stack, gera um relatório de anti-patterns com severidade e arquivo:linha, pede confirmação e só então reestrutura o código e valida que a aplicação sobe e que os endpoints continuam respondendo. Use quando pedirem auditoria de arquitetura, refatoração para MVC ou limpeza de código legado.
disable-model-invocation: true
---

# refactor-arch

Você vai auditar e refatorar o projeto da pasta atual em três fases, nesta ordem. O conhecimento de domínio está em `references/`. Em cada fase, leia os arquivos indicados **antes** de agir.

## Regras gerais

1. O projeto é a pasta de onde a skill foi chamada. Não altere nada fora dela, exceto o relatório em `reports/` (Fase 2).
2. **Nenhum arquivo é criado, alterado ou apagado nas Fases 1 e 2.** Só leitura e comandos que não escrevem.
3. Não mexa em `.claude/`, `.git/`, `node_modules/`, ambientes virtuais nem em relatórios antigos de outros projetos.
4. Não faça commit nem push. Quem versiona é o usuário.
5. Nunca imprima o conteúdo de arquivos `.env`.
6. Tudo o que você afirmar precisa de evidência no código. Se não souber, diga "não detectado".
7. Nada nesta skill depende de um projeto específico. Descubra nomes de arquivos, rotas e comandos a cada execução.

---

## Fase 1 — Análise

Leia `references/project-analysis.md`.

1. Liste os arquivos-fonte, ignorando o que a referência manda ignorar. Conte arquivos e linhas.
2. Detecte linguagem, framework e versão, dependências de runtime e banco de dados, sempre a partir do arquivo de dependências e dos imports.
3. Encontre o entry point, a porta, o comando de instalação, o comando para subir e scripts de seed.
4. Monte o inventário de rotas: método, caminho completo (com prefixos), `arquivo:linha` e campos esperados na entrada.
5. Liste as tabelas, deduza o domínio e classifique a arquitetura atual.
6. Imprima o bloco `PHASE 1: PROJECT ANALYSIS` no formato da seção 10 da referência, seguido do inventário de rotas.

Siga direto para a Fase 2.

## Fase 2 — Auditoria

Leia `references/anti-patterns.md` e `references/report-template.md`.

1. Leia todos os arquivos-fonte da lista da Fase 1, linha a linha. Não audite por amostragem.
2. Para cada anti-pattern do catálogo, procure os sinais de detecção. Anote cada ocorrência com `arquivo:linha` exato. Confira o número da linha no arquivo antes de escrever.
3. Agrupe ocorrências do mesmo anti-pattern num só finding, com todas as linhas.
4. Verifique APIs deprecated (AP-15) contra as versões detectadas na Fase 1.
5. Ordene de CRITICAL para LOW e confira se o `Summary` e o `Total` batem com a lista.
6. Imprima o relatório exatamente no formato do template.
7. Imprima `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e **encerre a sua resposta aqui**. Espere o usuário responder. Não chame nenhuma ferramenta de edição, não rode instalação e não suba a aplicação antes da resposta.

Respostas:
- **"n"** (ou qualquer recusa): diga que nada foi alterado e pare.
- **"y"**: grave o relatório seguindo a seção "Gravação do arquivo" do template e informe o caminho. Depois siga para a Fase 3.

## Fase 3 — Refatoração

Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`. Use os exemplos do playbook da linguagem detectada.

### 3.1 Baseline (antes de mudar o código)

1. Crie uma pasta temporária fora do projeto (`mktemp -d`) para guardar o baseline e os logs. Nada disso vai para dentro do projeto.
2. Instale as dependências com o comando descoberto na Fase 1. Em Python, use um ambiente virtual dentro do projeto (`.venv/`) se ainda não houver um.
3. Garanta um estado inicial limpo dos dados: se o banco é um arquivo, guarde uma cópia e recrie-o; rode o seed se o projeto tiver um.
4. Confira se a porta está livre. Suba a aplicação original em segundo plano, com a saída indo para um log, e espere a porta responder (no máximo ~20 s). Leia o começo do log: se houver erro, mostre ao usuário e pare.
5. Monte a lista de requisições a partir do inventário de rotas: use exemplos do projeto (`*.http`, README) quando existirem; para POST/PUT, monte corpos com os campos que o código lê e ids que existem no seed. Inclua pelo menos um caso de erro esperado (id inexistente ou corpo inválido). Ordem: leituras, criações, atualizações, remoções e, por último, rotas destrutivas (reset, delete em massa).
6. Execute as requisições com `curl` e grave método, rota, status e os campos da resposta (chaves do JSON ou o texto). Pare a aplicação.

### 3.2 Refatoração

1. Defina a estrutura alvo pela seção 2 das guidelines. Em projeto já organizado, siga a seção 8 (mapear o que existe e ajustar, sem reescrever do zero).
2. Aplique as transformações do playbook para cada finding do relatório, na ordem sugerida no playbook.
3. Preserve o contrato da API e o comando para rodar (seção 1 das guidelines).
4. Atualize os scripts que importam módulos movidos (seed, testes) e o arquivo de dependências, se algo mudar.
5. Anote cada exceção de segurança que muda uma resposta (ex.: campo `senha` removido, rota admin exigindo token).

### 3.3 Validação

1. Volte os dados ao mesmo estado inicial do baseline: apague o banco criado no 3.1 (banco em memória recomeça sozinho ao reiniciar).
2. Se o projeto tem seed, rode-o com o código novo. Ele precisa terminar sem erro.
3. Suba a aplicação refatorada pelo **mesmo comando** da Fase 1. Leia o começo do log: erro de import ou de boot é falha.
4. Rode as mesmas requisições do baseline e compare: mesmo status e mesmos campos. Diferenças só são aceitas se estiverem na lista de exceções de segurança.
5. Se algo falhar, corrija o código e repita a partir do passo 1. Faça no máximo 5 ciclos; se ainda falhar, pare e mostre ao usuário o que quebrou.
6. Pare a aplicação e apague o banco criado na validação, se ele não existia antes. Restaure a cópia guardada no 3.1, se havia uma.
7. Releia o código novo contra o catálogo e liste o que ainda restar. Não declare "zero anti-patterns" sem ter conferido.

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
  ✓ All endpoints respond correctly (<n>/<n> requests match baseline)
  ✓ Zero anti-patterns remaining

## Security exceptions
<cada mudança de resposta aceita e o motivo, ou "none">

## Validation log
<método rota → status antes | status depois, uma linha por requisição>
================================
```

Use `✗` em qualquer item que não passou e explique o motivo logo abaixo (ex.: `✗ 2 anti-patterns remaining: AP-16 em ..., AP-17 em ...`). Nunca marque `✓` sem ter rodado a verificação.
