# Conventional Commits

## O que é
**Conventional Commits** é um padrão para escrever mensagens de commit de forma clara, consistente e profissional.

Ele facilita:
- leitura do histórico
- code review
- automação de versões (Semantic Versioning)
- manutenção do projeto

---

## Estrutura do commit
Formato:

    <tipo>(escopo opcional): descrição curta

Exemplo:

    feat(auth): add JWT authentication

---

## Tipos mais usados

### feat
Nova funcionalidade (impacta o produto/usuário).

    feat: add password reset endpoint
    feat(auth): implement JWT authentication

### fix
Correção de bug.

    fix: prevent division by zero
    fix(api): return 404 when user not found

### refactor
Refatoração sem alterar comportamento (sem “feature” nem “bugfix”).

    refactor: simplify user service logic
    refactor(auth): extract token validation

### chore
Tarefas internas que não mudam comportamento do produto (config, deps, scripts).

    chore: update dependencies
    chore: configure pre-commit hooks

### docs
Apenas documentação.

    docs: update README
    docs(api): document auth endpoints

### test
Criação/ajuste de testes.

    test: add unit tests for auth service
    test(api): add integration tests for login

### style
Formatação/estilo (não muda lógica).

    style: fix lint issues
    style: format code with black

### build / ci
Build, pipeline, ferramentas e infraestrutura do projeto.

    build: update Dockerfile
    ci: add GitHub Actions pipeline

---

## Boas práticas
- Use verbo no imperativo (add, fix, update, remove)
- Mensagem curta (ideal ~50 caracteres na primeira linha)
- Commits em inglês (padrão comum em times)
- Um commit = uma mudança lógica
- Evite mensagens genéricas

---

## Exemplos de histórico bem feito

    feat(auth): add login endpoint
    feat(auth): generate JWT token
    fix(auth): handle invalid credentials
    test(auth): add login integration tests
    refactor(auth): extract token service
    docs: document authentication flow

---

## O que evitar
- update things
- final version
- ajustes
- wip
- Nunca inclua Claude Code (ou qualquer IA) como co-autor (`Co-Authored-By: Claude ...`) nas mensagens de commit

---

## Resumo
✔ Padrão simples  
✔ Histórico limpo  
✔ Mais fácil revisar e manter  

Use Conventional Commits sempre que possível.