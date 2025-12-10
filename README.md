# 📊 Gestão de Demandas de Projeto

Um aplicativo web interativo construído com **Streamlit** para registrar, organizar e acompanhar demandas de projeto com suporte a **Kanban**, **múltiplas etapas** e **integração com Google Sheets**.

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
- 💾 **Google Sheets Integration**: Sincronize todos os dados com Google Sheets
- 🔄 **Sincronização Automática**: Salve mudanças em tempo real
- 📥 **Importação/Exportação**: Carregue dados de qualquer lugar

## 🚀 Como Começar

### Pré-requisitos
- Python 3.8+
- Conta do Google (para usar Google Sheets)

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

   a. Vá para [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Crie um novo projeto
   
   c. Ative a API do Google Sheets
   
   d. Crie uma conta de serviço e baixe as credenciais em JSON
   
   e. Salve o arquivo como `config/credentials.json`
   
   f. Compartilhe uma planilha do Google com o email da conta de serviço

5. **Execute o aplicativo**
```bash
streamlit run app.py
```

O aplicativo será aberto em `http://localhost:8501`

## 📁 Estrutura do Projeto

```
App para gestão de demandas/
├── app.py                          # Aplicação principal
├── requirements.txt                # Dependências Python
├── README.md                       # Este arquivo
├── config/
│   └── credentials.json            # Credenciais Google (não versionado)
└── src/
    ├── modules/
    │   ├── models.py              # Modelos de dados (Projeto, Demanda, Etapa)
    │   ├── google_sheets_manager.py # Integração com Google Sheets
    │   └── kanban.py              # Lógica de visualização Kanban
    ├── components/
    │   └── ui_components.py       # Componentes reutilizáveis (cards, formulários)
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
- Mude status com drag-and-drop
- Filtre por projeto ou responsável
- Edite ou delete demandas rapidamente

### Gerenciar (Aba 3)
Três sub-abas:

#### Projetos
- Crie novos projetos
- Edite informações do projeto
- Veja todas as demandas associadas
- Delete projetos (remove também demandas associadas)

#### Demandas
- Crie demandas com título, descrição, prioridade
- Atribua responsáveis e datas de vencimento
- Adicione tags para categorização
- Edite ou delete demandas

#### Etapas
- Crie etapas customizadas (Design, Dev, Testes, etc.)
- Ordene etapas por sequência
- Adicione descrições
- Delete etapas

### Configurações (Aba 4)
- Sincronize com Google Sheets
- Salve dados no Google Sheets
- Limpe dados locais
- Informações sobre o aplicativo

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

- Credenciais do Google Sheets são armazenadas localmente em `config/credentials.json`
- Nunca commite credenciais no repositório
- Adicione `config/credentials.json` ao `.gitignore`

## 🛠️ Desenvolvido com

- **Streamlit** 1.28.1 - Framework web interativo
- **gspread** 5.10.0 - Cliente Google Sheets
- **pandas** 2.1.3 - Manipulação de dados
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
