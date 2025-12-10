# 🚀 DEPLOY - Comandos Prontos para Copiar e Colar

## 1️⃣ Preparar Git Local

```bash
cd "App para gestão de demandas"

# Inicializar Git
git init

# Adicionar todos os arquivos
git add .

# Verificar o que vai ser commitado (credentials.json NÃO deve aparecer!)
git status

# Fazer primeiro commit
git commit -m "Initial commit: app de gestão de demandas com Streamlit"

# Verificar que está tudo certo
git log --oneline
```

## 2️⃣ Conectar ao GitHub

```bash
# Substitua SEU-USUARIO e SEU-REPOSITORIO pelos seus valores!

git remote add origin https://github.com/SEU-USUARIO/app-gestao-demandas.git
git branch -M main
git push -u origin main
```

## 3️⃣ Deploy no Streamlit Cloud

1. Vá em: https://share.streamlit.io
2. Clique em "Sign in with GitHub"
3. Clique em "New app"
4. Preencha:
   - Repository: `SEU-USUARIO/app-gestao-demandas`
   - Branch: `main`
   - Main file path: `app.py`
5. Clique "Deploy"

## 4️⃣ Configurar Secrets

**Opção A: Via interface (mais fácil)**

1. Na página do seu app no Streamlit Cloud
2. Clique em "⚙️ Settings" (canto superior direito)
3. Vá para "Secrets"
4. Cole o conteúdo do seu `credentials.json` (arquivo local)
5. Clique "Save"

**Opção B: Via arquivo (se preferir)**

Na pasta do projeto, crie `.streamlit/secrets.toml`:

```toml
[google_sheets]
spreadsheet_id = "1cyZg-dt1BR4K7pTKvx5o8rWKP7_uNHrDQDdlYedTQI0"
credentials_json = "{conteúdo completo do seu credentials.json}"
```

Depois faça commit e push:
```bash
git add .streamlit/secrets.toml
git commit -m "Add secrets template"
git push origin main
```

## ✅ Verificação Final

Após deploy, verifique:

```bash
# 1. Verificar que credentials.json NÃO está no GitHub
git ls-files | grep credentials
# (não deve retornar nada)

# 2. Verificar status do repositório
git status
# (deve estar limpo: "On branch main, nothing to commit")
```

## 🔄 Atualizações Futuras

Sempre que fizer mudanças:

```bash
# Verificar mudanças
git status

# Adicionar arquivos modificados
git add .

# Fazer commit com mensagem descritiva
git commit -m "Feature: descrição do que foi adicionado"

# Enviar para GitHub (Streamlit Cloud fará redeploy automaticamente)
git push origin main
```

## 📱 URLs Importantes

- **Seu App:** `https://[seu-usuario]-app-gestao-demandas.streamlit.app`
- **Streamlit Cloud Dashboard:** https://share.streamlit.io
- **Seu Repositório GitHub:** `https://github.com/[seu-usuario]/app-gestao-demandas`

## ⏱️ Tempo Estimado

- Configurar Git: 2 minutos
- Fazer commit: 1 minuto
- Push para GitHub: 1 minuto
- Deploy no Streamlit Cloud: 2-3 minutos
- Configurar secrets: 2 minutos
- **Total: ~10 minutos**

## 🎯 Resultado Final

Seu app estará rodando em produção! 🚀

```
✅ Backend: Google Sheets (sincronização automática)
✅ Frontend: Streamlit Cloud (na nuvem)
✅ Dados: Persistidos no Google Sheets
✅ Usuários: Podem acessar via URL pública
```

---

**Pronto? Comece pelo Passo 1! 👆**
