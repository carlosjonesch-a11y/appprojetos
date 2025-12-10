# 🚀 Deployment - Instruções Rápidas

## Antes de fazer deploy: Configurar Google Sheets

⚠️ O app precisa de credenciais do Google para funcionar!

**Siga o guia:** `GOOGLE_SHEETS_SETUP.md` (5 minutos)

Resumo:
1. Criar conta de serviço no Google Cloud
2. Baixar chave JSON → salvar como `credentials.json` na raiz
3. Compartilhar planilha Google Sheets com a conta de serviço
4. Atualizar `SPREADSHEET_ID` em `src/modules/google_sheets_manager.py` (se usar outra planilha)

## ✅ Testar Localmente

```bash
# Verificar conexão
python -c "from src.modules.google_sheets_manager import GoogleSheetsManager; gsm = GoogleSheetsManager('credentials.json'); print('✅ Conectado!')"

# Rodar app
streamlit run app.py
```

Acesse: http://localhost:8501

Se vir os dados carregados → está pronto para deploy!

## O que foi removido?

❌ **Deletado 22+ arquivos desnecessários:**
- Scripts de teste/desenvolvimento
- Docs de setup antiga
- Pasta config/ com credenciais duplicadas
- Scripts run.bat e run.sh

## ✅ Projeto Final (11.6 MB)

```
App para gestão de demandas/
├── .streamlit/config.toml          ← Tema e configurações
├── src/                            ← Código da aplicação
├── app.py                          ← Entrada principal
├── requirements.txt                ← 10 dependências essenciais
├── credentials.json                ← Local only (não commitar)
├── README.md                       ← Documentação
├── GOOGLE_SHEETS_SETUP.md          ← Configuração Google
└── DEPLOY_CHECKLIST.md             ← Guia de deploy
```

## 🎯 Deploy em 3 passos

### 1️⃣ Fazer Commit
```bash
git add .
git commit -m "Production ready: projeto limpo e otimizado"
git push origin main
```

### 2️⃣ Deploy no Streamlit Cloud
- Vá em https://share.streamlit.io
- Clique "New app"
- Repo: seu-usuario/seu-repo
- Branch: main
- Main file: app.py

### 3️⃣ Configurar Secrets
- Settings → Secrets
- Adicione seu `credentials.json` em formato JSON
- Salve

## ⚡ Pronto!

Seu app estará disponível em:
```
https://seu-usuario-streamlit.streamlit.app
```

---

**Tempo de deploy:** ~2-3 minutos  
**Custo:** Gratuito (até certos limites)  
**Performance:** Excelente para 100+ usuários simultâneos
