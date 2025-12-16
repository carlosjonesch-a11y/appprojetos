# Guia de Configuração - Streamlit Cloud

## ✅ Status Local
- ✅ Estrutura da planilha criada com 5 abas:
  - projetos
  - demandas
  - etapas
  - checklist_topics
  - checklist_tasks
- ✅ App testado localmente e funcionando
- ✅ Código enviado para GitHub (commit 4e04ea9)

## 📋 Configurar no Streamlit Cloud

### 1. Acesse o Streamlit Cloud
https://share.streamlit.io/

### 2. Vá nas Configurações do App
- Clique no app **appprojetos**
- Clique em **⚙️ Settings** → **Secrets**

### 3. Configure os Secrets

Cole o conteúdo completo do arquivo `.streamlit/secrets.toml` (que está na sua máquina local).

**Importante:**
- Copie TODO o conteúdo de `.streamlit/secrets.toml`
- Cole no campo de Secrets do Streamlit Cloud
- Troque `ADMIN_PASSWORD` por uma senha forte

O formato deve ser:
```toml
GSHEETS_SPREADSHEET_ID = "1cyZg-dt1BR4K7pTKvx5o8rWKP7_uNHrDQDdlYedTQI0"

GOOGLE_SERVICE_ACCOUNT_JSON = '''
{
  ... (conteúdo do JSON do service account) ...
}
'''

ADMIN_PASSWORD = "SuaSenhaForte123!"
```

### 4. Salve e aguarde
- Clique em **Save**
- O Streamlit Cloud vai rebuildar automaticamente
- Aguarde 2-3 minutos

### 5. Teste
- Acesse seu app
- Vá em **Configurações** → **Testar conexão Google Planilhas**
- Deve mostrar: ✅ "Conexão com Google Planilhas funcionando!"

## 🎯 Próximos Passos

Após confirmar que está funcionando:
1. Crie alguns projetos para testar
2. Adicione etapas
3. Crie demandas e mova no Kanban
4. Teste o Check-list

## 📧 Compartilhamento da Planilha

A planilha já está compartilhada com:
- **conta-890@phrasal-catwalk-255413.iam.gserviceaccount.com** (Editor)

Não precisa fazer mais nada!

## 🔒 Segurança

- ✅ Arquivo JSON de credenciais está no `.gitignore`
- ✅ Não foi enviado para o GitHub
- ✅ Apenas está em `.streamlit/secrets.toml` (local) e Streamlit Cloud Secrets

---

**Status:** ✅ Pronto para deploy no Streamlit Cloud!
