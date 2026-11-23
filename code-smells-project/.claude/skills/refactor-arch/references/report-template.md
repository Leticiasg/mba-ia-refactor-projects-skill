# Template do relatório de auditoria (Fase 2)

O relatório é impresso no terminal e, depois da confirmação, gravado em arquivo. O conteúdo é o mesmo nos dois casos.

## Regras

- Findings ordenados por severidade: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, o de maior impacto primeiro.
- Todo finding tem `File:` com arquivo e linha exatos. Vários lugares: `File: models.py:28, 48-49; app.py:7`.
- O título do finding é o nome do anti-pattern no catálogo, seguido do ID (`AP-02`).
- `Description` diz o que está no código, com o trecho ou valor que comprova. `Impact` diz o que pode dar errado. `Recommendation` aponta a transformação do playbook (`T02`).
- Não esconda segredo do código na `Description` se ele já está hardcoded no repositório: cite onde está. Se for uma chave de produção real, mostre só os 4 primeiros caracteres.
- Finding possível (evidência parcial, ver `anti-patterns.md`): acrescente `(possible)` no fim do título e termine a `Description` com `Not confirmed: <o que falta verificar>`. Falsos positivos não entram no relatório.
- O `Summary` e o `Total` precisam bater com a lista de findings.
- APIs deprecated entram como findings normais (AP-15). Se não houver nenhuma, escreva a linha `Deprecated APIs: none detected` antes do total.

## Formato

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<linhas> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern> (AP-xx)
File: <arquivo>:<linha ou faixa>[, <arquivo>:<linha>]
Description: <o que está no código>
Impact: <o que pode dar errado>
Recommendation: <o que fazer> (playbook Txx)

### [HIGH] ...

### [MEDIUM] ...

### [LOW] ...

================================
Total: <n> findings
================================
```

## Exemplo de finding preenchido

```
### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 48-49, 110
Description: Queries montadas por concatenação com valores da requisição, ex.: "SELECT * FROM usuarios WHERE email = '" + email + "'".
Impact: Um e-mail como ' OR '1'='1 faz login sem senha; o mesmo vale para leitura e escrita.
Recommendation: Trocar por consultas parametrizadas com placeholders (playbook T02).
```

## Pausa obrigatória

Logo depois do bloco do relatório, imprima e espere a resposta:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Nada é criado ou alterado antes da resposta.

## Gravação do arquivo

Só depois que o usuário responder "y".

1. Descubra a raiz do repositório: `git rev-parse --show-toplevel`. Sem git, use a pasta pai do projeto.
2. Crie `reports/` na raiz, se não existir.
3. Se algum `reports/audit-project-*.md` contém a linha `Project: <nome da pasta do projeto>`, sobrescreva esse arquivo.
4. Se não, grave em `reports/audit-project-<N>.md`, com N = maior número existente + 1 (ou 1).
5. O arquivo contém o relatório dentro de um bloco de código, exatamente como foi impresso, sem a pergunta de confirmação.

Se a resposta for "n", não grave nada e encerre.
