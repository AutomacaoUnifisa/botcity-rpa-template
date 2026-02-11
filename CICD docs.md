# 🚀 Como Aplicar CI/CD em um Projeto BotCity

Guia prático para configurar CI/CD com GitHub Actions em projetos BotCity existentes.

---

## 📋 Cenário

Você já tem um bot funcionando localmente com essa estrutura:

```
meu-bot/
├── bot.py
├── requirements.txt
├── build.sh
├── build.bat
└── resources/
```

Vamos adicionar CI/CD para automatizar o deploy!

---

## 📝 Passo a Passo

### 1. Criar a pasta do workflow

No terminal, dentro da pasta do seu projeto:

```bash
mkdir -p .github/workflows
```

---

### 2. Criar o arquivo de workflow

```bash
# Linux/Mac
touch .github/workflows/deploy.yml

# Windows
echo. > .github\workflows\deploy.yml
```

---

### 3. Editar o arquivo deploy.yml

Abra `.github/workflows/deploy.yml` e cole:

```yaml
name: Deploy Bot
on: 
  push:
    branches: [main]

jobs:
  BotCity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Dar permissão ao build
        run: chmod +x build.sh
      
      - name: Build do bot
        run: ./build.sh
      
      - name: Deploy no Maestro
        uses: botcity-dev/botcity-action-bots@latest
        with:
          update: true
          deploy: false
          release: true
          version: '1.0.${{ github.run_number }}'
          botId: 'MeuBot'  # ⚠️ MUDE AQUI para o ID do seu bot
          technology: 'python'
          botPath: './dist/bot.zip'  # ⚠️ Ajuste se seu build gera em outro lugar
        env:
          LOGIN: ${{ secrets.LOGIN }}
          SERVER: ${{ secrets.SERVER }}
          KEY: ${{ secrets.KEY }}
```

**⚠️ AJUSTE 2 COISAS:**
- `botId: 'MeuBot'` → Coloque o ID do seu bot no Maestro
- `botPath: './dist/bot.zip'` → Veja onde seu `build.sh` gera o arquivo

---

### 4. Verificar onde o build gera o arquivo

Rode o build localmente:

```bash
./build.sh  # ou build.bat no Windows
```

Veja onde foi criado o `.zip`:
- Se criou em `dist/bot.zip` → use `'./dist/bot.zip'`
- Se criou em `bot.zip` na raiz → use `'./bot.zip'`

---

### 5. Configurar o repositório no GitHub

#### Se ainda NÃO tem repositório:

```bash
# Inicializa git
git init

# Adiciona remote (substitua SEU_USUARIO e SEU_REPO)
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git

# Cria branch main
git checkout -b main
```

#### Se já tem repositório:

```bash
# Só adiciona os arquivos novos
git status  # Vê o que mudou
```

---

### 6. Configurar Secrets no GitHub

1. Vá no seu repositório no GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Clique em **"New repository secret"** 3 vezes:

#### Secret 1:
- Name: `SERVER`
- Value: [Cole o Workspace do Maestro → Ambiente do desenvolvedor]

#### Secret 2:
- Name: `LOGIN`
- Value: [Cole o Login do Maestro]

#### Secret 3:
- Name: `KEY`
- Value: [Cole a Chave do Maestro]

---

### 7. Fazer o primeiro deploy via CI/CD

```bash
# Adiciona o workflow
git add .github/

# (Opcional) Adiciona outros arquivos se precisar
git add .

# Commit
git commit -m "feat: adiciona CI/CD com GitHub Actions"

# Push
git push origin main
```

---

### 8. Acompanhar a execução

1. Vá no GitHub → aba **Actions**
2. Você verá o workflow rodando
3. Clique nele para ver os logs

---

### 9. Verificar no Maestro

1. Maestro → **Robôs**
2. Procure seu bot
3. Você verá a nova versão `1.0.1`
4. Ela deve estar marcada como **"Release Version"**

---

## ✅ Pronto! Agora é automático

A partir de agora, **toda vez que você fizer**:

```bash
git add .
git commit -m "fix: corrige validação"
git push origin main
```

**O GitHub automaticamente:**
1. ✅ Faz build
2. ✅ Deploy no Maestro
3. ✅ Marca como release
4. ✅ Versão incrementa sozinha (1.0.2, 1.0.3...)

---

## 🔧 Casos Especiais

### Se for a PRIMEIRA VEZ (bot não existe no Maestro)

#### Opção 1: Criar manualmente primeiro (Recomendado)

1. Crie o bot via **Easy Deploy** no Maestro
2. Anote o **botId** que você usou
3. Configure o CI/CD normalmente

#### Opção 2: Criar via CI/CD

Ajuste o workflow para criar na primeira execução:

```yaml
update: false
deploy: true   # ← Mude para true
release: true
```

Após a primeira execução, volte para:

```yaml
update: true
deploy: false
```

---

### Se você trabalha em branches de feature

```yaml
on: 
  push:
    branches: [main]  # Só faz deploy da main
  pull_request:
    branches: [main]  # Testa PRs mas não faz deploy
```

Ou crie dois workflows separados:
- `test.yml` → Roda testes em qualquer branch
- `deploy.yml` → Só faz deploy da main

---

### Se você tem múltiplos bots no mesmo repositório

Crie múltiplos jobs no mesmo workflow:

```yaml
jobs:
  Bot1:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: chmod +x build.sh
      - run: ./build.sh
      - name: Deploy Bot 1
        uses: botcity-dev/botcity-action-bots@latest
        with:
          botId: 'Bot1'
          botPath: './dist/bot1.zip'
          # ... demais configurações

  Bot2:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: chmod +x build.sh
      - run: ./build.sh
      - name: Deploy Bot 2
        uses: botcity-dev/botcity-action-bots@latest
        with:
          botId: 'Bot2'
          botPath: './dist/bot2.zip'
          # ... demais configurações
```

---

## 🐛 Troubleshooting

### Erro: "Permission denied" no build.sh

**Solução:**
```bash
# No seu projeto, rode:
chmod +x build.sh
git add build.sh
git commit -m "fix: permissão do build.sh"
git push
```

---

### Erro: "bot.zip not found"

**Causa:** O workflow não encontrou o arquivo no caminho especificado

**Solução:**
1. Veja onde seu `build.sh` cria o arquivo (rode localmente)
2. Ajuste o `botPath` no workflow:
   - `'./dist/bot.zip'` se cria em dist/
   - `'./bot.zip'` se cria na raiz
   - `'./build/bot.zip'` se cria em build/

---

### Erro: "Bot not found"

**Causa:** O bot não existe no Maestro ou o ID está errado

**Solução:**
1. Verifique no Maestro → Robôs qual é o ID exato do bot
2. Confirme que o `botId` no workflow é **exatamente igual** (maiúsculas/minúsculas importam)
3. Se o bot não existe, use `deploy: true` na primeira execução

---

### Erro: "Invalid credentials"

**Causa:** Secrets configurados incorretamente

**Solução:**
1. Vá em Settings → Secrets and variables → Actions
2. Verifique se os 3 secrets existem: `SERVER`, `LOGIN`, `KEY`
3. Certifique-se que copiou corretamente do Maestro (sem espaços extras)
4. Se necessário, delete e recrie os secrets

---

### Workflow não executa

**Causa:** Arquivo no lugar errado ou sintaxe incorreta

**Solução:**
1. Confirme que o arquivo está em `.github/workflows/deploy.yml` (caminho completo)
2. Valide a sintaxe YAML (use um validador online ou a própria interface do GitHub)
3. Verifique se a branch de push é a `main` (ou ajuste o `on: push: branches`)

---

## 📊 Estrutura Final do Projeto

Depois de configurar, seu projeto ficará assim:

```
meu-bot/
├── .github/
│   └── workflows/
│       └── deploy.yml        ← Novo arquivo
├── bot.py
├── requirements.txt
├── build.sh
├── build.bat
├── resources/
└── dist/                     ← Gerado pelo build
    └── bot.zip
```

---

## 🎯 Resumo Rápido

1. ✅ Cria `.github/workflows/deploy.yml`
2. ✅ Ajusta `botId` e `botPath`
3. ✅ Configura 3 secrets no GitHub
4. ✅ Push e pronto! 🎉

**Nunca mais deploy manual!**

---

## 📚 Recursos Adicionais

- [Documentação oficial BotCity Actions](https://github.com/botcity-dev/botcity-action-bots)
- [Documentação GitHub Actions](https://docs.github.com/en/actions)
- [Documentação BotCity Maestro](https://documentation.botcity.dev/)
