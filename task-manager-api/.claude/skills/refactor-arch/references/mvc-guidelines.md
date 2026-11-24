# Guidelines de arquitetura MVC (Fase 3)

O padrão alvo da refatoração. Vale para qualquer stack; os nomes de arquivo seguem a convenção da linguagem (`snake_case.py`, `camelCase.js`).

**Seções:** Princípios · Estrutura alvo · Responsabilidades e proibições · Fluxo de uma requisição · Erros · Configuração · Banco e dados · Projeto já parcialmente organizado · Checklist da Fase 3.

## Princípios

1. **O contrato da API não muda.** Mesma rota, mesmo método, mesmo status e mesmos campos na resposta. A única exceção é uma correção de segurança justificada (ex.: tirar `senha` da resposta, exigir token numa rota administrativa ou na edição dos dados de um usuário). Toda exceção aparece no resumo final da Fase 3.
2. **O comando para rodar não muda.** Se era `python app.py` ou `npm start`, continua sendo.
3. **Mudança mínima em projeto já organizado.** Se uma pasta já cumpre o papel de uma camada, mantenha e corrija o conteúdo. Não reescreva do zero o que só precisa de ajuste.
4. **Sem dependência nova sem necessidade.** Prefira a biblioteca padrão e o que já está instalado. Se uma dependência for indispensável, adicione ao arquivo de dependências e instale.
5. **Os dados continuam no mesmo lugar.** O banco precisa ser criado e lido no mesmo arquivo de antes, e os scripts de seed continuam funcionando.

## Estrutura alvo

### Python (Flask)

```
<projeto>/
├── app.py                      # entry point fino: from src.app import create_app; app = create_app(); app.run(...)
├── requirements.txt
├── .env.example                # nomes das variáveis de ambiente, sem valores reais
└── src/
    ├── __init__.py
    ├── app.py                  # composition root: create_app()
    ├── config/
    │   └── settings.py
    ├── models/
    │   └── <entidade>_model.py
    ├── views/
    │   └── <entidade>_routes.py   # Blueprints
    ├── controllers/
    │   └── <entidade>_controller.py
    ├── services/                  # só se houver integração externa
    │   └── <integracao>_service.py
    └── middlewares/
        └── error_handler.py
```

### Node.js (Express)

```
<projeto>/
├── package.json                # "start" continua apontando para o entry point
├── .env.example
└── src/
    ├── app.js                  # composition root: cria o app, liga tudo, chama listen
    ├── config/
    │   └── settings.js
    ├── models/
    │   └── <entidade>Model.js
    ├── views/
    │   └── <entidade>Routes.js    # express.Router()
    ├── controllers/
    │   └── <entidade>Controller.js
    ├── services/
    │   └── <integracao>Service.js
    └── middlewares/
        └── errorHandler.js
```

Se o projeto já tem `src/` ou pastas equivalentes (`routes/` no lugar de `views/`), adapte em vez de duplicar. O que importa é a responsabilidade de cada camada, e não o nome da pasta. Registre a equivalência no resumo final.

## Responsabilidades e proibições

| Camada | Faz | Não pode |
|---|---|---|
| **Config** (`config/`) | Lê variáveis de ambiente, define valores padrão seguros para desenvolvimento, centraliza constantes de domínio (status válidos, limites) | Ter segredo real escrito no código; importar models ou rotas |
| **Model** (`models/`) | Acesso a dados (SQL parametrizado ou ORM), mapeamento linha → objeto/dicionário, regras que dependem só da entidade (ex.: `is_overdue`) | Ler `request`/`req`; montar resposta HTTP; chamar serviços externos; SQL concatenado |
| **View / Routes** (`views/`) | Define rotas e métodos, lê corpo/query/params, chama o controller, devolve o status e o JSON | Ter SQL; ter regra de negócio; decidir regra de status além de mapear o resultado |
| **Controller** (`controllers/`) | Coordena o caso de uso: valida a entrada, chama models e services, aplica regra de negócio, controla a transação, lança erros de domínio | Ter SQL; conhecer `request`/`req`/`res`; formatar JSON |
| **Service** (`services/`) | Fala com sistemas de fora: e-mail, SMS, gateway de pagamento | Acessar o banco; ser usado direto pela rota |
| **Middleware** (`middlewares/`) | Tratamento de erro central, autenticação de rotas administrativas, log de requisição | Regra de negócio |
| **Composition root** (`app.py` / `app.js`) | Cria a app, carrega config, inicializa o banco, registra rotas e middlewares | Ter rota com lógica; ter SQL; ter regra de negócio |

Numa API JSON não existe template HTML: a **View** é a camada HTTP (rota + formato da resposta).

## Fluxo de uma requisição

```
HTTP → View (lê a entrada) → Controller (valida, aplica regra, coordena) → Model (dados)
                                     └→ Service (integração externa)
Controller devolve dados ou lança erro → View monta o status e o JSON
Qualquer erro não tratado → middleware de erro → JSON padronizado
```

## Erros

- Defina erros de domínio (ex.: `NotFoundError` → 404, `ValidationError` → 400, `UnauthorizedError` → 401).
- O controller lança; o middleware/handler central converte em JSON.
- O handler central loga o erro completo e devolve uma mensagem genérica para 500. Nunca devolva `str(e)` ou stack trace.
- Mantenha os campos de erro que o projeto já usa (`erro`, `error`, `sucesso`, `msg`), para não quebrar o contrato.

## Configuração

- Segredos e ambiente vêm de variáveis de ambiente (`os.environ.get`, `process.env`).
- Valor padrão só para o que não é segredo (porta, caminho do banco de desenvolvimento).
- Para `SECRET_KEY` sem variável definida: gere um valor aleatório na inicialização (`secrets.token_hex(32)`, `crypto.randomBytes(32)`) e avise no log. Não escreva um valor fixo.
- `DEBUG` vem do ambiente e é desligado por padrão.
- Crie `.env.example` com os nomes das variáveis e valores de exemplo que não sejam reais.

## Banco e dados

- Uma conexão por requisição (Flask: `g` + `teardown_appcontext`) ou injetada no model pelo composition root. Nada de conexão global alterada por `global`.
- Operações com várias gravações ficam numa transação, controlada pelo controller ou por uma função do model.
- Ao mover a app para `src/`, confirme o caminho do banco: o Flask-SQLAlchemy cria SQLite relativo em `instance/` ao lado do módulo da app. Fixe o caminho (absoluto a partir da raiz do projeto ou `instance_path`) para o arquivo continuar onde estava.
- Atualize scripts que importam módulos movidos (seed, testes) e rode-os para conferir.
- Se a forma de guardar senha mudar (hash forte), o seed precisa gravar no formato novo e o login dos usuários de exemplo precisa continuar funcionando com as senhas originais.

## Projeto já parcialmente organizado

1. Mapeie cada pasta existente para uma camada (ex.: `routes/` → View; `models/` → Model; `services/` → Service se for integração externa, senão Controller; `utils/` → Config para constantes, ou removido se for código morto).
2. Mova para controllers a lógica que está nas rotas.
3. Mova para os models as consultas que estão nas rotas.
4. Crie o que falta: `config/`, `controllers/`, `middlewares/error_handler`.
5. Corrija os findings da Fase 2 dentro de cada camada.

## Checklist da Fase 3

- [ ] Estrutura de diretórios segue esta guideline (ou a equivalência foi registrada)
- [ ] Configuração extraída para `config/`, sem segredo hardcoded
- [ ] Models abstraem os dados; SQL só neles e sempre parametrizado
- [ ] Views/Routes só recebem e respondem
- [ ] Controllers concentram o fluxo
- [ ] Error handling centralizado
- [ ] Entry point claro e comando de execução igual ao original
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem com o mesmo status e os mesmos campos (exceções de segurança listadas)
