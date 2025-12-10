# 📋 CHECKLIST PARA DEPLOY NO STREAMLIT CLOUD

## ✅ Pré-Deploy (Local)
- [ ] Todos os `use_container_width` foram convertidos para `width="stretch"` 
- [ ] Sintaxe Python validada em todos os módulos
- [ ] `requirements.txt` contém apenas dependências necessárias
- [ ] `credentials.json` não está commitado (está em `.gitignore`)
- [ ] Código testado localmente em `http://localhost:8501`
- [ ] Não há erros ou warnings em produção

## 🔐 Configuração de Secrets (Streamlit Cloud)

1. **Na dashboard do Streamlit Cloud:**
   - Vá em Settings → Secrets
   - Cole o conteúdo de `secrets.toml.example`
   - Substitua os valores com suas credenciais do Google Cloud
   - **NUNCA** faça commit do `secrets.toml` com valores reais

2. **Estrutura esperada:**
```toml
[google_sheets]
spreadsheet_id = "1cyZg-dt1BR4K7pTKvx5o8rWKP7_uNHrDQDdlYedTQI0"
credentials_json = "{...}"
```

## 📦 Deployment Steps

1. **Push para GitHub:**
```bash
git add .
git commit -m "Deploy: corrigir use_container_width e preparar para produção"
git push origin main
```

2. **Conectar no Streamlit Cloud:**
   - Vá em https://share.streamlit.io
   - Clique "New app"
   - Selecione seu repositório GitHub
   - Branch: `main`
   - Main file path: `app.py`
   - Clique "Deploy"

3. **Configurar Secrets:**
   - Após deploy, vá em "Advanced settings"
   - Cole suas credenciais Google em "Secrets"
   - Salve e aguarde redeployment automático

## 🧪 Testes Pós-Deploy

- [ ] App carrega sem erros em Streamlit Cloud
- [ ] Dashboard exibe corretamente
- [ ] Gantt Chart com todos os níveis funcionando
- [ ] Kanban View atualizando demandas
- [ ] Filtros e drill-down operacionais
- [ ] Google Sheets sincronizando dados corretamente

## 📊 Dados Iniciais

O projeto já contém dados populados:
- ✅ 5 Projetos
- ✅ 4 Etapas
- ✅ 47+ Demandas

Nenhum script adicional é necessário para inicializar.

## 🔄 Atualizações Futuras

Para atualizar o app após deploy:
1. Faça alterações localmente
2. Teste em `http://localhost:8501`
3. Commit e push para GitHub
4. Streamlit Cloud fará deploy automaticamente

## ❌ Troubleshooting

**App não conecta no Google Sheets:**
- Verifique o `spreadsheet_id` nos Secrets
- Verifique que `credentials.json` está correto
- Confirme que a service account tem acesso à planilha

**Erros de timeout:**
- Verifique conexão com internet
- Google Sheets API pode estar lenta
- Tente recarregar a página

**Widgets duplicados:**
- Limpe o cache: `streamlit cache clear`
- Verifique se todos os `key=` são únicos no código

## 📚 Arquivos Importantes

```
App para gestão de demandas/
├── app.py                          # Entrada principal
├── requirements.txt                # Dependências
├── credentials.json               # NÃO COMMITAR (local only)
├── .gitignore                     # Já contém credentials.json
├── .streamlit/
│   ├── config.toml               # Configuração de tema
│   └── secrets.toml.example      # Template de secrets
├── src/
│   ├── modules/
│   │   ├── models.py             # Data models
│   │   ├── google_sheets_manager.py
│   │   ├── gantt.py              # Gantt charts
│   │   └── kanban.py             # Kanban view
│   └── components/
│       └── ui_components.py      # UI elements
└── [scripts de desenvolvimento - não necessários em produção]
```

## ✨ Status Final

✅ Pronto para deploy em Streamlit Cloud
✅ Todos os warnings corrigidos
✅ Dados iniciais populados
✅ Autenticação Google configurada
