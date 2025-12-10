# 🚀 DEPLOY STREAMLIT CLOUD - Guia Completo

## ✅ Status Pré-Deploy

```
✅ Projeto limpo e otimizado
✅ 10 dependências essenciais em requirements.txt
✅ Sintaxe Python validada
✅ credentials.json protegido em .gitignore
✅ App funcionando localmente em http://localhost:8501
✅ Dados sincronizados com Google Sheets
```

## 📋 Passo 1: Preparar Repositório Git

### 1.1 Inicializar Git (se ainda não feito)
```bash
cd "App para gestão de demandas"
git init
git add .
git commit -m "Initial commit: projeto de gestão de demandas"
```

### 1.2 Criar repositório no GitHub
1. Vá em https://github.com/new
2. Nome: `app-gestao-demandas`
3. Descrição: "App para gestão de demandas com Streamlit"
4. Privado ou Público (recomenda privado)
5. Clique "Create repository"

### 1.3 Conectar repositório local ao GitHub
```bash
git remote add origin https://github.com/SEU-USUARIO/app-gestao-demandas.git
git branch -M main
git push -u origin main
```

⚠️ **Importante:** Certifique-se de que `credentials.json` NÃO está sendo commitado:
```bash
git status
# credentials.json NÃO deve aparecer na lista
```

## 🌐 Passo 2: Deploy no Streamlit Cloud

### 2.1 Acessar Streamlit Cloud
1. Vá em https://share.streamlit.io
2. Clique em "Sign in with GitHub" (ou crie conta)
3. Autorize Streamlit a acessar seus repositórios

### 2.2 Criar novo app
1. Clique em "New app" (botão azul no canto superior esquerdo)
2. Preencha:
   - **Repository:** seu-usuario/app-gestao-demandas
   - **Branch:** main
   - **Main file path:** app.py
3. Clique "Deploy"

### 2.3 Aguardar deployment
- Status: `Running` (geralmente 1-2 minutos)
- Você verá logs em tempo real
- URL será gerada automaticamente: `https://seu-usuario-app-gestao-demandas.streamlit.app`

## 🔐 Passo 3: Configurar Secrets

### 3.1 Acessar configuração de secrets
1. Na página do seu app no Streamlit Cloud, clique em "⚙️ Settings"
2. Vá para "Secrets"
3. Cole o conteúdo abaixo

### 3.2 Adicionar credenciais Google
Clique no campo de texto e cole:

```toml
[google_sheets]
spreadsheet_id = "1cyZg-dt1BR4K7pTKvx5o8rWKP7_uNHrDQDdlYedTQI0"
credentials_json = """
{
  "type": "service_account",
  "project_id": "seu-projeto-id",
  "private_key_id": "sua-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA\n-----END PRIVATE KEY-----\n",
  "client_email": "app-gestao-demandas@seu-projeto-id.iam.gserviceaccount.com",
  "client_id": "seu-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
"""
```

**Aonde pegar esses valores:**
- Abra seu arquivo `credentials.json` local
- Copie TODO o conteúdo (entre `{` e `}`)
- Cole em `credentials_json` acima

### 3.3 Salvar secrets
- Clique "Save" (botão azul)
- Streamlit Cloud fará redeploy automaticamente (~30-60s)
- Você verá mensagem: "Updated secrets for ..."

## ✅ Passo 4: Validar Deploy

### 4.1 Acessar seu app
- URL: `https://seu-usuario-app-gestao-demandas.streamlit.app`
- Aguarde carregar (~5-10 segundos primeira vez)

### 4.2 Verificar funcionalidades
- ✅ Dashboard carrega com métricas
- ✅ Dados do Google Sheets aparecem
- ✅ Gantt Chart mostra projetos
- ✅ Kanban Board funciona
- ✅ Filtros respondem

Se tudo aparecer → **Deploy bem-sucedido!** 🎉

## 🔄 Atualizações Futuras

Depois do deploy inicial, para atualizar seu app:

1. Faça mudanças localmente
2. Teste em `http://localhost:8501`
3. Commit e push:
   ```bash
   git add .
   git commit -m "Feature: descrição da mudança"
   git push origin main
   ```
4. Streamlit Cloud fará redeploy automaticamente (2-3 minutos)

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| "ModuleNotFoundError" | Verifique `requirements.txt` tem todas as dependências |
| "File not found: credentials.json" | Secrets não foram configurados. Vá em Settings → Secrets |
| "Permission denied" | A conta de serviço Google não tem acesso à planilha |
| "App carrega lentamente" | Google Sheets API pode estar lenta. Tente recarregar |
| "Dados não aparecem" | Verifique `spreadsheet_id` está correto nos secrets |

## 📊 Estrutura Final Deployada

```
App para gestão de demandas/ (GitHub)
├── .streamlit/config.toml
├── src/
│   ├── modules/
│   │   ├── models.py
│   │   ├── google_sheets_manager.py
│   │   ├── gantt.py
│   │   └── kanban.py
│   └── components/
│       └── ui_components.py
├── app.py
├── requirements.txt
├── README.md
├── GOOGLE_SHEETS_SETUP.md
├── DEPLOYMENT.md
└── .gitignore (protege credentials.json)

Streamlit Cloud (Runtime)
├── Lê app.py e dependências
├── Carrega secrets (credentials)
├── Conecta ao Google Sheets
└── Exibe app em https://seu-app.streamlit.app
```

## 🎯 URLs Úteis

- **Seu app:** https://seu-usuario-app-gestao-demandas.streamlit.app
- **Dashboard Streamlit:** https://share.streamlit.io
- **Google Cloud Console:** https://console.cloud.google.com
- **Repositório GitHub:** https://github.com/seu-usuario/app-gestao-demandas

## 💡 Dicas Finais

1. **Compartilhe seu app:** URL acima pode ser compartilhada com qualquer pessoa
2. **Monitore performance:** Na dashboard do Streamlit Cloud você vê logs e uso
3. **Limite de uso:** Plano gratuito tem limite de ~1GB/mês de data transfer
4. **Segurança:** Nunca comite `credentials.json` no GitHub
5. **Backups:** Google Sheets é seu backup automático

---

**Tempo total:** ~15-20 minutos  
**Resultado:** App profissional rodando na nuvem! ☁️✨

**Seu app estará disponível em:**
```
🚀 https://seu-usuario-app-gestao-demandas.streamlit.app
```
