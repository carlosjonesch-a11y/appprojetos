# 📊 Gestão de Demandas de Projeto

Um aplicativo web interativo construído com **Streamlit** para registrar, organizar e acompanhar demandas de projeto com suporte a **Kanban**, **múltiplas etapas**, **Dashboard** e persistência em **Google Planilhas**.

## ✨ Funcionalidades

### Core
- ✅ **Gerenciamento de Projetos**: Crie e organize múltiplos projetos
- 📋 **Gerenciamento de Demandas**: Crie demandas com título, descrição, prioridade e status
- 🎯 **Etapas de Projeto**: Defina etapas customizadas para cada projeto
- 📝 **Atribuição**: Atribua responsáveis e datas de vencimento

### Visualização & Tracking
- 📊 **Dashboard**: Métricas em tempo real com gráficos de status e prioridade
- 📈 **Kanban Interativo**: Visualize demandas em colunas por status (A Fazer, Em Progresso, Em Revisão, Concluído)
- 🔄 **Atualização de Status**: Mude status diretamente no Kanban
- 📱 **Interface Responsiva**: Design adaptável para diferentes tamanhos de tela

### Persistência de Dados
- 💾 **Google Planilhas**: Persistência via gspread + google-auth (service account)
- 🔄 **Sincronização**: Salva mudanças automaticamente na planilha
- ✅ **Check-list**: Sistema de tópicos e tarefas persistido na mesma planilha

## 🚀 Como Começar

### Pré-requisitos
- Python 3.8+
- Conta Google com acesso ao Google Sheets
- Service Account do Google Cloud (para autenticação)

### Instalação

1. **Clone o repositório**
```bash
cd "App para gestão de demandas"
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/Scripts/activate  # No Windows
# ou
source venv/bin/activate  # No macOS/Linux
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure o Google Sheets**

**Passo 1: Criar Service Account**
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto (ou use um existente)
3. Ative a API do Google Sheets e Google Drive
4. Vá em "IAM & Admin" > "Service Accounts" > "Create Service Account"
5. Dê um nome e clique em "Create and Continue"
6. Pule as permissões opcionais e clique em "Done"
7. Clique no service account criado > "Keys" > "Add Key" > "Create new key" > JSON
8. Baixe o arquivo JSON (guarde com segurança!)

**Passo 2: Compartilhar a Planilha**
1. Abra sua planilha no Google Sheets
2. Clique em "Compartilhar"
3. Cole o email do service account (está no JSON como `client_email`)
4. Dê permissão de "Editor"
5. Copie o ID da planilha da URL (entre `/d/` e `/edit`)

**Passo 3: Configurar Secrets**
- Crie o arquivo `.streamlit/secrets.toml` (baseado no `.streamlit/secrets.toml.example`)
- Cole o conteúdo do JSON do service account em `GOOGLE_SERVICE_ACCOUNT_JSON`
- Cole o ID da planilha em `GSHEETS_SPREADSHEET_ID`

5. **Execute o aplicativo**
```bash
streamlit run app.py
```

O aplicativo será aberto em `http://localhost:8501`

**Execução com script (PowerShell):**
```powershell
# Inicia Streamlit em uma porta livre (por padrão 8501)
./scripts/run_streamlit.ps1
# Inicia Streamlit a partir de outra porta de base (exemplo 8591)
./scripts/run_streamlit.ps1 -StartPort 8591
# Força matar processo que ocupa a porta (caso necessário)
./scripts/stop_streamlit_on_port.ps1 -Port 8501
```

**Executar via VS Code (atalho):**
- Pressione `Ctrl+Shift+B` para executar a tarefa padrão (Run Streamlit (default))
- Ou pressione `F1` e escolha `Tasks: Run Task` para selecionar uma das variantes

### Deploy no Streamlit Cloud

1. Faça push do código para GitHub
2. Conecte seu repositório no [Streamlit Cloud](https://streamlit.io/cloud)
3. Em "Settings" > "Secrets", cole o conteúdo completo do `.streamlit/secrets.toml`
4. Deploy!

**⚠️ Importante:**
- Nunca faça commit do arquivo `.streamlit/secrets.toml` (já está no `.gitignore`)
- Mantenha o JSON do service account seguro
- A planilha precisa estar compartilhada com o service account

## 📁 Estrutura do Projeto

```
App para gestão de demandas/
├── app.py                          # Aplicação principal
├── requirements.txt                # Dependências Python
├── README.md                       # Este arquivo
└── src/
    ├── modules/
    │   ├── models.py              # Modelos de dados (Projeto, Demanda, Etapa)
    │   ├── google_sheets_manager.py  # Persistência no Google Sheets
    │   ├── gantt.py               # Gráficos (Gantt / Curva S)
    │   ├── kanban.py              # Lógica de visualização Kanban
    │   └── checklist.py           # Sistema de check-list com tópicos/tarefas
    ├── components/
    │   └── ui_components2.py      # Componentes reutilizáveis (cards, formulários)
    └── utils/
        └── (para funções utilitárias)
```

## 🎯 Guia de Uso

### Dashboard (Aba 1)
- Visualize métricas resumidas
- Gráficos de status e prioridade
- Taxa de conclusão de projetos
- Previsão de atraso (Curva S)
- Gantt interativo com drilldown

### Kanban (Aba 2)
- Visualize demandas organizadas por status
- Filtre por projeto ou etapa
- Edite ou delete demandas rapidamente

### Configurações (Aba 3)
- Informações de conexão com Google Sheets
- Teste de conectividade
- Sincronização manual
- Limpeza de dados

### Gerenciar (Aba 4)
- Protegido por senha (ADMIN_PASSWORD)
- Cadastro de projetos, etapas e demandas
- Geração de dados de teste (seed)

### Check-list (Aba 5)
- Crie tópicos de checklist
- Adicione tarefas por tópico
- Marque tarefas como concluídas
- Persistido automaticamente no Google Sheets

## 📊 Modelos de Dados

### Projeto
```python
{
    "id": "abc123",
    "nome": "Nome do Projeto",
    "descricao": "Descrição",
    "status": "A Fazer",  # A Fazer, Em Progresso, Em Revisão, Concluído
    "responsavel": "João Silva",
    "data_criacao": "2025-01-10T10:30:00",
    "data_conclusao": "2025-12-31T00:00:00"
}
```

### Demanda
```python
{
    "id": "dem001",
    "titulo": "Implementar login",
    "descricao": "Sistema de autenticação com Google",
    "projeto_id": "abc123",
    "status": "Em Progresso",
    "prioridade": "Alta",  # Baixa, Média, Alta, Urgente
    "responsavel": "Maria Santos",
    "etapa_id": "etapa001",
    "data_vencimento": "2025-01-15T00:00:00",
    "data_criacao": "2025-01-10T10:30:00",
    "data_conclusao": null,
    "tags": ["backend", "autenticação"],
    "comentarios": ["Aguardando review"]
}
```

### Etapa
```python
{
    "id": "etapa001",
    "nome": "Desenvolvimento",
    "descricao": "Etapa de desenvolvimento do projeto",
    "ordem": 2,
    "data_criacao": "2025-01-10T10:30:00"
}
```

## 🔐 Segurança

- Não commite credenciais do banco no repositório.
- No Streamlit Cloud, use **Secrets** para definir `DATABASE_URL`.

## 🛠️ Desenvolvido com

- **Streamlit** 1.41.1 - Framework web interativo
- **SQLAlchemy** 2.x - ORM
- **pg8000** - Driver Postgres (pure-Python)
- **pandas** - Manipulação de dados
- **Python** 3.8+ - Linguagem

## 📈 Próximas Funcionalidades

- [ ] Sistema de filtros mais avançados
- [ ] Comentários colaborativos em demandas
- [ ] Anexos de arquivos
- [ ] Relatórios em PDF
- [ ] Sistema de notificações
- [ ] Timeline de atividades
- [ ] Integração com API de terceiros
- [ ] Tema escuro/claro

## 🤝 Contribuindo

Sinta-se à vontade para contribuir com melhorias, correções de bugs ou novas funcionalidades!

## 📄 Licença

Este projeto está sob licença MIT.

## 📞 Suporte

Para dúvidas ou problemas, abra uma issue ou entre em contato.

---

**Desenvolvido com ❤️ usando Streamlit**

*Última atualização: 10 de dezembro de 2025*
