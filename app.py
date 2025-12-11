import streamlit as st
import uuid
from datetime import datetime
import os
from src.modules.models import Projeto, Demanda, Etapa, StatusEnum, PriorityEnum
from src.modules.google_sheets_manager import GoogleSheetsManager
from src.components.ui_components import (
    create_projeto_card, create_demanda_card, create_demanda_form,
    create_projeto_form, create_etapa_form
)
from src.modules.kanban import KanbanView, DashboardMetrics
from src.modules.gantt import GanttChart

# Configuração da página
st.set_page_config(
    page_title="Gestão de Demandas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS customizados
st.markdown("""
    <style>
    .main {
        padding: 0;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2em;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização de estado
if "projetos" not in st.session_state:
    st.session_state.projetos = []

if "demandas" not in st.session_state:
    st.session_state.demandas = []

if "etapas" not in st.session_state:
    st.session_state.etapas = []

if "google_sheets_manager" not in st.session_state:
    try:
        # Primeiro tenta usar Streamlit secrets (Streamlit Cloud)
        if "GOOGLE_CREDENTIALS" in st.secrets:
            credentials = dict(st.secrets["GOOGLE_CREDENTIALS"])
            st.session_state.google_sheets_manager = GoogleSheetsManager(credentials)
        # Se não houver secrets, tenta arquivo local (desenvolvimento)
        elif os.path.exists("credentials.json"):
            st.session_state.google_sheets_manager = GoogleSheetsManager("credentials.json")
        else:
            st.session_state.google_sheets_manager = None
            st.warning("⚠️ Credenciais não encontradas. Configure as secrets no Streamlit Cloud.")
    except Exception as e:
        st.session_state.google_sheets_manager = None
        st.warning(f"⚠️ Erro ao conectar Google Sheets: {str(e)[:100]}")

if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = False

if "demanda_em_edicao" not in st.session_state:
    st.session_state.demanda_em_edicao = None

if "projeto_em_edicao" not in st.session_state:
    st.session_state.projeto_em_edicao = None

# Carregar dados automaticamente na primeira execução
if "dados_carregados" not in st.session_state:
    st.session_state.dados_carregados = False
    if st.session_state.google_sheets_manager:
        try:
            st.session_state.projetos = st.session_state.google_sheets_manager.load_projetos()
            st.session_state.demandas = st.session_state.google_sheets_manager.load_demandas()
            st.session_state.etapas = st.session_state.google_sheets_manager.load_etapas()
            st.session_state.dados_carregados = True
        except Exception as e:
            st.warning(f"⚠️ Erro ao carregar dados: {str(e)[:100]}")

# ============= FUNÇÕES AUXILIARES =============

def carregar_dados():
    """Carrega dados do Google Sheets"""
    if st.session_state.google_sheets_manager:
        try:
            with st.spinner("Carregando dados..."):
                st.session_state.projetos = st.session_state.google_sheets_manager.load_projetos()
                st.session_state.demandas = st.session_state.google_sheets_manager.load_demandas()
                st.session_state.etapas = st.session_state.google_sheets_manager.load_etapas()
            st.success("Dados carregados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

def salvar_dados():
    """Salva dados no Google Sheets"""
    if st.session_state.google_sheets_manager:
        try:
            with st.spinner("Salvando dados..."):
                st.session_state.google_sheets_manager.save_projetos(st.session_state.projetos)
                st.session_state.google_sheets_manager.save_demandas(st.session_state.demandas)
                st.session_state.google_sheets_manager.save_etapas(st.session_state.etapas)
            st.success("Dados salvos com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar dados: {e}")

def criar_projeto(dados_form: dict):
    """Cria um novo projeto"""
    novo_projeto = Projeto(
        id=str(uuid.uuid4())[:8],
        nome=dados_form["nome"],
        descricao=dados_form["descricao"],
        responsavel=dados_form["responsavel"],
        status=dados_form["status"],
        data_conclusao=dados_form.get("data_conclusao")
    )
    st.session_state.projetos.append(novo_projeto)
    salvar_dados()
    st.success(f"Projeto '{novo_projeto.nome}' criado com sucesso!")

def editar_projeto(projeto_id: str, dados_form: dict):
    """Edita um projeto existente"""
    for i, p in enumerate(st.session_state.projetos):
        if p.id == projeto_id:
            st.session_state.projetos[i].nome = dados_form["nome"]
            st.session_state.projetos[i].descricao = dados_form["descricao"]
            st.session_state.projetos[i].responsavel = dados_form["responsavel"]
            st.session_state.projetos[i].status = dados_form["status"]
            st.session_state.projetos[i].data_conclusao = dados_form.get("data_conclusao")
            break
    salvar_dados()
    st.success("Projeto atualizado com sucesso!")

def deletar_projeto(projeto_id: str):
    """Deleta um projeto"""
    st.session_state.projetos = [p for p in st.session_state.projetos if p.id != projeto_id]
    st.session_state.demandas = [d for d in st.session_state.demandas if d.projeto_id != projeto_id]
    salvar_dados()
    st.success("Projeto deletado com sucesso!")

def criar_demanda(dados_form: dict, demanda_id: str = None):
    """Cria ou atualiza uma demanda"""
    if demanda_id:
        # Editar demanda existente
        for i, d in enumerate(st.session_state.demandas):
            if d.id == demanda_id:
                st.session_state.demandas[i].titulo = dados_form["titulo"]
                st.session_state.demandas[i].descricao = dados_form["descricao"]
                st.session_state.demandas[i].status = dados_form["status"]
                st.session_state.demandas[i].prioridade = dados_form["prioridade"]
                st.session_state.demandas[i].responsavel = dados_form["responsavel"]
                st.session_state.demandas[i].etapa_id = dados_form.get("etapa_id")
                st.session_state.demandas[i].data_vencimento = dados_form.get("data_vencimento")
                st.session_state.demandas[i].data_inicio_plano = dados_form.get("data_inicio_plano")
                st.session_state.demandas[i].data_vencimento_plano = dados_form.get("data_vencimento_plano")
                st.session_state.demandas[i].data_inicio_real = dados_form.get("data_inicio_real")
                st.session_state.demandas[i].data_vencimento_real = dados_form.get("data_vencimento_real")
                st.session_state.demandas[i].tags = dados_form.get("tags", [])
                break
        st.success("Demanda atualizada com sucesso!")
    else:
        # Criar nova demanda
        nova_demanda = Demanda(
            id=str(uuid.uuid4())[:8],
            titulo=dados_form["titulo"],
            descricao=dados_form["descricao"],
            projeto_id=dados_form["projeto_id"],
            status=dados_form["status"],
            prioridade=dados_form["prioridade"],
            responsavel=dados_form["responsavel"],
            etapa_id=dados_form.get("etapa_id"),
            data_vencimento=dados_form.get("data_vencimento"),
            data_inicio_plano=dados_form.get("data_inicio_plano"),
            data_vencimento_plano=dados_form.get("data_vencimento_plano"),
            data_inicio_real=dados_form.get("data_inicio_real"),
            data_vencimento_real=dados_form.get("data_vencimento_real"),
            tags=dados_form.get("tags", [])
        )
        st.session_state.demandas.append(nova_demanda)
        st.success(f"Demanda '{nova_demanda.titulo}' criada com sucesso!")
    
    salvar_dados()

def deletar_demanda(demanda_id: str):
    """Deleta uma demanda"""
    st.session_state.demandas = [d for d in st.session_state.demandas if d.id != demanda_id]
    salvar_dados()
    st.success("Demanda deletada com sucesso!")

def mudar_status_demanda(demanda_id: str, novo_status: str):
    """Muda o status de uma demanda"""
    for d in st.session_state.demandas:
        if d.id == demanda_id:
            d.status = novo_status
            if novo_status == "Concluído":
                d.data_conclusao = datetime.now().isoformat()
            break
    salvar_dados()
    st.rerun()

def criar_etapa(dados_form: dict, etapa_id: str = None):
    """Cria ou atualiza uma etapa"""
    if etapa_id:
        for i, e in enumerate(st.session_state.etapas):
            if e.id == etapa_id:
                st.session_state.etapas[i].nome = dados_form["nome"]
                st.session_state.etapas[i].descricao = dados_form["descricao"]
                st.session_state.etapas[i].ordem = dados_form["ordem"]
                break
        st.success("Etapa atualizada com sucesso!")
    else:
        nova_etapa = Etapa(
            id=str(uuid.uuid4())[:8],
            nome=dados_form["nome"],
            descricao=dados_form["descricao"],
            ordem=dados_form["ordem"]
        )
        st.session_state.etapas.append(nova_etapa)
        st.success(f"Etapa '{nova_etapa.nome}' criada com sucesso!")
    
    salvar_dados()

def deletar_etapa(etapa_id: str):
    """Deleta uma etapa"""
    st.session_state.etapas = [e for e in st.session_state.etapas if e.id != etapa_id]
    salvar_dados()
    st.success("Etapa deletada com sucesso!")

# ============= INTERFACE PRINCIPAL =============

# Header
col1, col2 = st.columns([3, 1])

with col1:
    st.title("📊 Gestão de Demandas de Projeto")
    st.markdown("*Organize suas demandas com eficiência e rastreie o progresso em tempo real*")

with col2:
    if st.button("🔄 Sincronizar Google Sheets"):
        carregar_dados()

# Verificação de credenciais
if not st.session_state.google_sheets_manager:
    st.warning("""
    ⚠️ **Google Sheets não configurado**
    
    Para sincronizar seus dados com Google Sheets:
    
    **1. Baixe o arquivo de credenciais:**
    - Acesse: https://console.cloud.google.com/iam-admin/serviceaccounts
    - Clique em sua conta de serviço
    - Vá para "KEYS" → "ADD KEY" → "Create new key" → "JSON"
    - Salve como: `config/credentials.json`
    
    **2. Compartilhe sua planilha:**
    - Email da conta: `serviceaccount@[seu-projeto].iam.gserviceaccount.com`
    - Permissão: Editor
    
    **Detalhes:** Veja `CONFIGURACAO_GOOGLE.md`
    """)
else:
    st.success("✅ Google Sheets conectado e pronto para sincronizar!")

st.markdown("---")

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "📋 Kanban", "✏️ Gerenciar", "⚙️ Configurações"])

# ============= TAB 1: DASHBOARD =============
with tab1:
    st.header("Dashboard Principal")
    
    if st.session_state.demandas or st.session_state.projetos:
        # Seção de métricas
        st.subheader("📊 Métricas")
        DashboardMetrics.render_metrics(st.session_state.projetos, st.session_state.demandas)
        
        st.divider()
        
        # Seção de Gantt
        st.subheader("📈 Cronograma (Gantt)")
        GanttChart.render_gantt_por_demanda(
            st.session_state.demandas,
            st.session_state.projetos,
            st.session_state.etapas
        )
        
        st.divider()
        
        # Seção de Curva S
        st.subheader("📊 Curva S (Planejado vs Realizado)")
        GanttChart.render_curva_s(
            st.session_state.demandas,
            st.session_state.projetos
        )
    else:
        st.info("Nenhum dado para exibir. Crie projetos e demandas para ver o dashboard.")

# ============= TAB 2: KANBAN =============
with tab2:
    st.header("📊 Visualização Kanban")
    
    if st.session_state.demandas:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_projeto = st.selectbox(
                "Filtrar por Projeto",
                options=[None] + [p.id for p in st.session_state.projetos],
                format_func=lambda x: "Todos" if x is None else next((p.nome for p in st.session_state.projetos if p.id == x), x),
                key="kanban_filtro_projeto"
            )
        
        with col2:
            responsaveis = list(set([d.responsavel for d in st.session_state.demandas if d.responsavel]))
            filtro_responsavel = st.selectbox(
                "Filtrar por Responsável",
                options=[None] + responsaveis,
                format_func=lambda x: "Todos" if x is None else x,
                key="kanban_filtro_responsavel"
            )
        
        with col3:
            if st.button("Atualizar Kanban"):
                st.rerun()
        
        st.markdown("---")
        
        # Kanban
        KanbanView.render_kanban(
            demandas=st.session_state.demandas,
            on_status_change=lambda d, novo_status: mudar_status_demanda(d.id, novo_status),
            on_edit=lambda d: st.session_state.update({"modo_edicao": True, "demanda_em_edicao": d}),
            on_delete=lambda d: deletar_demanda(d.id),
            filtro_projeto=filtro_projeto,
            filtro_responsavel=filtro_responsavel
        )
    else:
        st.info("Nenhuma demanda para exibir. Crie demandas na aba 'Gerenciar'.")

# ============= TAB 3: GERENCIAR =============
with tab3:
    subtab1, subtab2, subtab3 = st.tabs(["Projetos", "Demandas", "Etapas"])
    
    # SUBTAB: PROJETOS
    with subtab1:
        st.header("🎯 Gerenciar Projetos")
        
        # Formulário de novo projeto
        if st.button("➕ Novo Projeto", key="novo_projeto_btn"):
            st.session_state.projeto_em_edicao = None
        
        with st.form("form_projeto", clear_on_submit=True):
            st.subheader("📝 Criar Novo Projeto")
            dados = create_projeto_form(st.session_state.projeto_em_edicao)
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ Criar Projeto")
            with col2:
                cancel = st.form_submit_button("❌ Cancelar")
            
            if submit:
                if dados["nome"]:
                    criar_projeto(dados)
                    st.rerun()
                else:
                    st.error("Nome do projeto é obrigatório")
            
            if cancel:
                st.rerun()
        
        # Lista de projetos
        st.subheader("Meus Projetos")
        
        if st.session_state.projetos:
            for idx, projeto in enumerate(st.session_state.projetos):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    #### {projeto.nome}
                    {projeto.descricao}
                    
                    **Status:** {projeto.status} | **Responsável:** {projeto.responsavel or 'Não atribuído'}
                    """)
                
                with col2:
                    if st.button("✏️", key=f"edit_proj_{projeto.id}_{idx}", help="Editar"):
                        st.session_state.projeto_em_edicao = projeto
                
                with col3:
                    if st.button("🗑️", key=f"delete_proj_{projeto.id}_{idx}", help="Deletar"):
                        deletar_projeto(projeto.id)
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("Nenhum projeto criado ainda.")
    
    # SUBTAB: DEMANDAS
    with subtab2:
        st.header("📋 Gerenciar Demandas")
        
        # Formulário de nova demanda
        if st.button("➕ Nova Demanda", key="nova_demanda_btn"):
            st.session_state.demanda_em_edicao = None
        
        with st.form("form_demanda", clear_on_submit=True):
            st.subheader("📝 " + ("Editar Demanda" if st.session_state.demanda_em_edicao else "Criar Nova Demanda"))
            
            dados = create_demanda_form(
                st.session_state.projetos,
                st.session_state.etapas,
                st.session_state.demanda_em_edicao
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ " + ("Atualizar" if st.session_state.demanda_em_edicao else "Criar Demanda"))
            with col2:
                cancel = st.form_submit_button("❌ Cancelar")
            
            if submit:
                if dados["titulo"] and dados["projeto_id"]:
                    criar_demanda(dados, st.session_state.demanda_em_edicao.id if st.session_state.demanda_em_edicao else None)
                    st.session_state.demanda_em_edicao = None
                    st.rerun()
                else:
                    st.error("Título e Projeto são obrigatórios")
            
            if cancel:
                st.session_state.demanda_em_edicao = None
                st.rerun()
        
        # Lista de demandas
        st.subheader("Minhas Demandas")
        
        if st.session_state.demandas:
            for idx, demanda in enumerate(st.session_state.demandas):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    #### {demanda.titulo}
                    {demanda.descricao}
                    
                    **Status:** {demanda.status} | **Prioridade:** {demanda.prioridade} | **Responsável:** {demanda.responsavel or 'Não atribuído'}
                    """)
                
                with col2:
                    if st.button("✏️", key=f"edit_dem_{demanda.id}_{idx}", help="Editar"):
                        st.session_state.demanda_em_edicao = demanda
                        st.rerun()
                
                with col3:
                    if st.button("🗑️", key=f"delete_dem_{demanda.id}_{idx}", help="Deletar"):
                        deletar_demanda(demanda.id)
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("Nenhuma demanda criada ainda.")
    
    # SUBTAB: ETAPAS
    with subtab3:
        st.header("🎯 Gerenciar Etapas")
        
        # Formulário de nova etapa
        with st.form("form_etapa", clear_on_submit=True):
            st.subheader("📝 Nova Etapa")
            dados = create_etapa_form()
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ Criar Etapa")
            with col2:
                cancel = st.form_submit_button("❌ Cancelar")
            
            if submit:
                if dados["nome"]:
                    criar_etapa(dados)
                    st.rerun()
                else:
                    st.error("Nome da etapa é obrigatório")
            
            if cancel:
                st.rerun()
        
        # Lista de etapas
        st.subheader("Minhas Etapas")
        
        if st.session_state.etapas:
            for idx, etapa in enumerate(st.session_state.etapas):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    #### {etapa.nome}
                    {etapa.descricao}
                    
                    **Ordem:** {etapa.ordem}
                    """)
                
                with col2:
                    if st.button("✏️", key=f"edit_etapa_{etapa.id}_{idx}", help="Editar"):
                        st.session_state.etapa_em_edicao = etapa
                
                with col3:
                    if st.button("🗑️", key=f"delete_etapa_{etapa.id}_{idx}", help="Deletar"):
                        deletar_etapa(etapa.id)
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("Nenhuma etapa criada ainda.")

# ============= TAB 4: CONFIGURAÇÕES =============
with tab4:
    st.header("⚙️ Configurações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Google Sheets")
        if st.button("🔄 Carregar dados do Google Sheets"):
            carregar_dados()
        
        if st.button("💾 Salvar dados no Google Sheets"):
            salvar_dados()
    
    with col2:
        st.subheader("Dados Locais")
        col_clear1, col_clear2 = st.columns(2)
        with col_clear1:
            if st.button("🗑️ Limpar Dados Locais"):
                st.session_state.projetos = []
                st.session_state.demandas = []
                st.session_state.etapas = []
                st.success("Dados locais limpos!")
                st.rerun()
    
    st.markdown("---")
    
    st.subheader("Sobre o Aplicativo")
    st.markdown("""
    **Gestão de Demandas de Projeto**
    
    Um aplicativo versátil e responsivo para registrar, organizar e acompanhar demandas de projeto.
    
    **Funcionalidades:**
    - ✅ Criação e gerenciamento de projetos
    - 📋 Criação e acompanhamento de demandas
    - 🎯 Definição de etapas de projeto
    - 📊 Dashboard com métricas
    - 📈 Visualização Kanban interativa
    - 💾 Integração com Google Sheets
    - 📱 Interface responsiva
    
    **Versão:** 1.0.0
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.85em;">
    <p>Desenvolvido com ❤️ usando Streamlit</p>
    <p><small>© 2025 Gestão de Demandas - Todos os direitos reservados</small></p>
</div>
""", unsafe_allow_html=True)
