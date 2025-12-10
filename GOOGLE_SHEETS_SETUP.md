# 🔐 Configuração Google Sheets - Setup Rápido

## ⚡ 3 Passos Simples

### 1️⃣ Criar Conta de Serviço no Google Cloud

1. Vá em: https://console.cloud.google.com
2. Selecione seu projeto (ou crie um novo)
3. Menu → **IAM e administração** → **Contas de serviço**
4. Clique em **+ Criar conta de serviço**
5. Preencha:
   - Nome: `app-gestao-demandas`
   - ID: `app-gestao-demandas` (auto)
   - Descrição: "App de gestão de demandas"
6. Clique **Criar**

### 2️⃣ Gerar Chave JSON

1. Na lista de contas, clique na conta criada
2. Vá para a aba **Chaves**
3. Clique **Adicionar chave** → **Criar nova chave** → **JSON**
4. O arquivo baixará automaticamente como `seu-projeto-id-xxxxx.json`
5. **Renomeie para** `credentials.json` e **salve na raiz do projeto**:
   ```
   App para gestão de demandas/
   ├── credentials.json   ← Aqui!
   ├── app.py
   ├── requirements.txt
   └── src/
   ```

### 3️⃣ Compartilhar Planilha Google Sheets

**Opção A: Usar planilha existente**
1. Abra sua planilha em https://sheets.google.com
2. Copie o ID da URL:
   ```
   https://docs.google.com/spreadsheets/d/ESTE-É-O-ID/edit
                                       ^^^^^^^^^^^^^^^^
   ```
3. Edite `src/modules/google_sheets_manager.py` na linha 9:
   ```python
   SPREADSHEET_ID = "COLE-SEU-ID-AQUI"
   ```

**Opção B: Usar a planilha de exemplo (já configurada)**
- O app já tem um ID pré-configurado
- Basta compartilhar a planilha existente com a conta de serviço

### 4️⃣ Compartilhar com a Conta de Serviço

1. Abra sua planilha Google Sheets
2. Clique **Compartilhar** (canto superior direito)
3. No Google Cloud Console, copie o email da conta:
   - Vá em: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Clique na conta `app-gestao-demandas`
   - Copie o email no formato: `app-gestao-demandas@seu-projeto.iam.gserviceaccount.com`
4. Cole na caixa de compartilhamento da planilha
5. Selecione **Editor** como permissão
6. Desmarque "Notificar pessoas"
7. Clique **Compartilhar**

## ✅ Verificar Configuração

Execute este comando na pasta do projeto:

```bash
python -c "from src.modules.google_sheets_manager import GoogleSheetsManager; gsm = GoogleSheetsManager('credentials.json'); print('✅ Conectado!'); print(f'Demandas carregadas: {len(gsm.load_demandas())}')"
```

Esperado:
```
✅ Conectado!
Demandas carregadas: 47
```

## 🛡️ Segurança

⚠️ **NUNCA commite `credentials.json`**
- Arquivo `.gitignore` já protege automaticamente
- É uma chave secreta de acesso!

Para **Streamlit Cloud**:
1. Em **Settings → Secrets**, adicione:
```toml
[google_sheets]
spreadsheet_id = "seu-id-aqui"
credentials_json = "{conteúdo completo do JSON}"
```

2. O app lerá automaticamente dos secrets

## 📋 Estrutura de Abas Necessárias

Sua planilha deve ter 3 abas (sheets):

### Aba 1: **Projetos**
| id | nome | descricao |
|----|------|-----------|
| P1 | Projeto A | Descrição |
| P2 | Projeto B | Descrição |

### Aba 2: **Etapas**
| id | nome | descricao |
|----|------|-----------|
| E1 | Planejamento | Descrição |
| E2 | Desenvolvimento | Descrição |

### Aba 3: **Demandas**
18 colunas obrigatórias (nesta ordem):
```
id, titulo, descricao, projeto_id, status, prioridade, responsavel, 
etapa_id, data_inicio_plano, data_inicio_real, data_vencimento_plano, 
data_vencimento_real, data_vencimento, data_criacao, data_conclusao, 
percentual_completo, tags, comentarios
```

**Status permitidos:** A Fazer, Em Progresso, Em Revisão, Concluído  
**Prioridades:** Baixa, Média, Alta, Crítica

## 🐛 Troubleshooting

| Erro | Solução |
|------|---------|
| "File not found: credentials.json" | Verifique se está na raiz (não em subpasta) |
| "Permission denied" | Compartilhe a planilha com o email da conta |
| "Spreadsheet not found" | O ID está errado. Copie novamente da URL |
| "Demandas vazias" | Verifique nomes das abas: "Projetos", "Etapas", "Demandas" |
| "401 Unauthorized" | A chave JSON expirou. Gere uma nova |

## 🚀 Resumo Rápido

1. ✅ Criar conta de serviço no Google Cloud
2. ✅ Baixar chave JSON → renomear para `credentials.json` → colocar na raiz
3. ✅ Compartilhar planilha com o email da conta
4. ✅ Atualizar `SPREADSHEET_ID` se necessário
5. ✅ Rodar app: `streamlit run app.py`
6. ✅ Reload na página → dados aparecem!

**Tempo total:** ~5 minutos  
**Resultado:** App sincronizado com Google Sheets ✨
