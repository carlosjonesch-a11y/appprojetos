# ✅ CHECKLIST PRÉ-DEPLOY - Verificação Final

## 🔍 Antes de começar

- [ ] Você tem conta no GitHub? (https://github.com)
- [ ] Você tem conta no Streamlit Cloud? (https://share.streamlit.io)
- [ ] Você tem conta no Google Cloud com credenciais configuradas?
- [ ] Arquivo `credentials.json` está na raiz do projeto?
- [ ] App está rodando localmente sem erros?

## 📋 Verificação de Arquivos

### Arquivos que DEVEM estar presentes:
- [ ] `app.py` (aplicação principal)
- [ ] `requirements.txt` (dependências)
- [ ] `credentials.json` (local apenas, não será commitado)
- [ ] `.gitignore` (protege credentials)
- [ ] `src/` pasta com módulos
- [ ] `.streamlit/config.toml` (tema)

### Arquivos que NÃO devem estar presentes:
- [ ] Nenhum arquivo `credentials` duplicado
- [ ] Nenhum `__pycache__` ou `.pyc`
- [ ] Nenhum `venv/` (exceto em .gitignore)
- [ ] Nenhum arquivo `.env` com secrets

## 🔐 Segurança

- [ ] `credentials.json` está em `.gitignore`?
- [ ] `credentials.json` NÃO será commitado? (execute: `git check-ignore credentials.json`)
- [ ] Nenhum outro arquivo com credenciais existe?
- [ ] Você nunca vai fazer commit de `credentials.json`?

## 🧪 Testes Funcionais

Antes de fazer deploy, teste:

```bash
# 1. Verificar sintaxe Python
python -m py_compile app.py

# 2. Verificar conexão com Google Sheets
python -c "from src.modules.google_sheets_manager import GoogleSheetsManager; print('✅ OK')"

# 3. Verificar imports
python -c "import streamlit; import plotly; import gspread; import pandas; print('✅ Dependências OK')"

# 4. Rodar app localmente
streamlit run app.py
```

Esperado:
- [ ] Sem erros de sintaxe
- [ ] Conexão com Google Sheets OK
- [ ] Todas as dependências carregam
- [ ] App abre em http://localhost:8501
- [ ] Dados aparecem no dashboard

## 📦 Git & GitHub

- [ ] Git está instalado? (`git --version`)
- [ ] Você criou repositório no GitHub?
- [ ] Nome do repositório: `app-gestao-demandas`
- [ ] Repositório é público ou privado? (recomenda privado)
- [ ] Você tem acesso de push ao repositório?

## 🌐 Streamlit Cloud

- [ ] Você tem conta no Streamlit Cloud?
- [ ] Você autorizou Streamlit Cloud a acessar GitHub?
- [ ] Você sabe seu usuário do Streamlit Cloud?

## 📝 Passos do Deploy

Siga em ordem:

### Passo 1: Git Local (5 minutos)
- [ ] Abra terminal na pasta do projeto
- [ ] Execute: `git init`
- [ ] Execute: `git add .`
- [ ] Execute: `git commit -m "Initial commit: app gestão demandas"`
- [ ] Verifique com: `git log --oneline`

### Passo 2: GitHub (5 minutos)
- [ ] Crie repositório em https://github.com/new
- [ ] Nome: `app-gestao-demandas`
- [ ] Conecte repositório local:
  ```bash
  git remote add origin https://github.com/SEU-USUARIO/app-gestao-demandas.git
  git branch -M main
  git push -u origin main
  ```
- [ ] Verifique em GitHub se arquivos apareceram
- [ ] Confirme que `credentials.json` NÃO está lá

### Passo 3: Streamlit Cloud Deploy (3 minutos)
- [ ] Acesse https://share.streamlit.io
- [ ] Clique "New app"
- [ ] Selecione seu repositório
- [ ] Configure:
  - Repository: `seu-usuario/app-gestao-demandas`
  - Branch: `main`
  - Main file: `app.py`
- [ ] Clique "Deploy"
- [ ] Aguarde status virar "Running"

### Passo 4: Configurar Secrets (3 minutos)
- [ ] Na página do app, clique "⚙️ Settings"
- [ ] Vá para "Secrets"
- [ ] Cole seu `credentials.json` completo
- [ ] Clique "Save"
- [ ] Aguarde redeploy automático
- [ ] Verifique que dados aparecem

### Passo 5: Validação Final (2 minutos)
- [ ] Acesse URL do seu app
- [ ] Verifique Dashboard carrega
- [ ] Verifique dados do Google Sheets aparecem
- [ ] Teste Gantt Chart (drill-down)
- [ ] Teste Kanban Board
- [ ] Teste filtros

## 🎯 Sucesso! 🎉

Se todos os itens acima estão marcados:

✅ **Seu app está em produção!**

- [ ] Compartilhar URL com time
- [ ] Documentar a URL em lugar seguro
- [ ] Fazer backup de credentials.json (local)
- [ ] Configurar notificações no Streamlit Cloud (opcional)

## 🆘 Se algo deu errado

| Problema | Solução |
|----------|---------|
| "Repository not found" | Verifique nome do repo no GitHub |
| "Build failed" | Veja logs no Streamlit Cloud → ajuste dependências |
| "Credentials error" | Verifique secrets estão corretos |
| "No data appears" | Verifique spreadsheet_id em google_sheets_manager.py |

**Para mais detalhes:** Veja `STREAMLIT_CLOUD_DEPLOY.md`

---

**Data de Deploy:** ___________  
**URL Final:** ___________  
**Status:** ___________
