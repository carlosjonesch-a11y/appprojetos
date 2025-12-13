# 📊 Gestão de Demandas de Projeto

Um aplicativo web interativo construído com **Streamlit** para registrar, organizar e acompanhar demandas de projeto com suporte a **Kanban**, **múltiplas etapas**, **Dashboard** e persistência em **Postgres**.

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
- 💾 **Postgres (recomendado)**: Persistência via SQLAlchemy + pg8000
- 🔄 **Sincronização**: Salva mudanças no banco quando conectado

## 🚀 Como Começar

---

## 📦 Deploy & Banco de Dados (considerações)
- **Banco local (localhost)**: se o Postgres estiver no seu PC em `localhost`, ele só funciona enquanto o PC estiver ligado.
- **Streamlit Cloud + banco local do seu PC**: não funciona. No Streamlit Cloud, `localhost` aponta para a máquina do Cloud, não para o seu computador.
- **Expor o banco do seu PC na internet** (port-forward/DDNS/IP fixo) até poderia permitir conexão, mas é frágil e inseguro para produção.

- **Como fazer deploy corretamente**:
  - Para rodar no Streamlit Cloud (ou outro provedor) use um banco de dados que seja acessível a partir da internet (Postgres remoto, Cloud SQL, ElephantSQL, Supabase, Amazon RDS, etc.).
  - Configure a variável `DATABASE_URL` nas `secrets` do Streamlit Cloud e garanta que o driver `pg8000` esteja definido em `requirements.txt`.
  - Se quiser testar com `localhost` em um portátil, você pode: (1) subir o Postgres localmente, (2) executar o app localmente usando `./scripts/run_streamlit.ps1`, mas não use `localhost` como DB no Streamlit Cloud.

- **Se o computador estiver desligado**: O banco local fica inacessível e qualquer app (local ou cloud) que dependa dele não funcionará (perda de persistência). Para produção/uso em nuvem, escolha um DB remoto.

---

## 🚀 Como Começar

### Pré-requisitos
- Python 3.8+
- Acesso a um Postgres (local para desenvolvimento ou remoto para deploy)

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

4. **Configure o Postgres**

- Configure `DATABASE_URL` com a string de conexão do Postgres.
    - Exemplo: `postgresql+pg8000://user:password@host:5432/dbname`

5. **Execute o aplicativo**
```bash
streamlit run app.py
```

O aplicativo será aberto em `http://localhost:8501`
Execução com script (PowerShell):
```powershell
# Inicia Streamlit em uma porta livre (por padrão 8501)
./scripts/run_streamlit.ps1
# Inicia Streamlit a partir de outra porta de base (exemplo 8591)
./scripts/run_streamlit.ps1 -StartPort 8591
# Força matar processo que ocupa a porta (caso necessário)
./scripts/stop_streamlit_on_port.ps1 -Port 8501
```

Executar via VS Code (atalho):
- Pressione `Ctrl+Shift+B` para executar a tarefa padrão (Run Streamlit (default)).
- Ou pressione `F1` e escolha `Tasks: Run Task` para selecionar uma das variantes (start 8591 / kill conflicts).

Se preferir abrir o app via Debug (Launch), use a configuração `Run Streamlit (task)` em Run and Debug → start.

Dica: o script `run_streamlit.ps1` encontra uma porta livre. Se você insistir em um número de porta (por exemplo 8591) e ela já estiver em uso, chame o script com `-KillConflicts` para parar o processo que usa o porto. Use com cautela.
Se for executar no Linux/macOS, o comando usual `streamlit run app.py --server.port 8501` funciona normalmente.
### Banco de Dados (Postgres)

- Configure `DATABASE_URL` com a string de conexão do Postgres.
    - Exemplo: `postgresql+pg8000://user:password@host:5432/dbname`
- No Streamlit Cloud, adicione `DATABASE_URL` em **Secrets**.

Nota: para evitar problemas de build no Streamlit Cloud, recomendamos usar o driver puro-Python `pg8000` (já está no `requirements.txt`).

## 📁 Estrutura do Projeto

```
App para gestão de demandas/
├── app.py                          # Aplicação principal
├── requirements.txt                # Dependências Python
├── README.md                       # Este arquivo
└── src/
    ├── modules/
    │   ├── models.py              # Modelos de dados (Projeto, Demanda, Etapa)
    │   ├── postgres_manager.py    # Persistência no Postgres
    │   ├── gantt.py               # Gráficos (Gantt / Curva S)
    │   └── kanban.py              # Lógica de visualização Kanban
    ├── components/
    │   └── ui_components2.py      # Componentes reutilizáveis (cards, formulários)
    ├── pages/
    │   └── (para futuros módulos de páginas)
    └── utils/
        └── (para funções utilitárias)
```

## 🎯 Guia de Uso

### Dashboard (Aba 1)
- Visualize métricas resumidas
- Gráficos de status e prioridade
- Taxa de conclusão de projetos

### Kanban (Aba 2)
- Visualize demandas organizadas por status
- Filtre por projeto ou responsável
- Edite ou delete demandas rapidamente

### Configurações (Aba 3)
- Informações de conexão
- Sincronização com o banco
- Limpeza de dados (memória / banco)

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
