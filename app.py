import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.modules.models import Projeto, Demanda, Etapa, StatusEnum, PriorityEnum
from src.modules.postgres_manager import PostgresManager
from src.components.ui_components import (
    create_projeto_card, create_demanda_card, create_projeto_form,
    create_demanda_form, create_etapa_form, show_status_badge, show_priority_badge
)
from src.modules.kanban import KanbanView, DashboardMetrics
from src.modules.gantt import GanttChart

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Gestão de Demandas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INITIALIZATION
# ============================================================================

# Database URL (Postgres)
DATABASE_URL = "postgresql+pg8000://postgres:!Enrico18@localhost:5432/jones"

# Initialize PostgresManager
if "db_manager" not in st.session_state:
    st.session_state.db_manager = PostgresManager(DATABASE_URL)

# Test connection on startup
if "db_connected" not in st.session_state:
    try:
        health = st.session_state.db_manager.health_check()
        st.session_state.db_connected = health.get("connected", False)
    except Exception as e:
        st.session_state.db_connected = False
        st.session_state.db_error = str(e)

# Load data from Postgres
if st.session_state.db_connected:
    if "projetos" not in st.session_state or st.session_state.get("reload_data", False):
        st.session_state.projetos = st.session_state.db_manager.load_projetos()
        st.session_state.demandas = st.session_state.db_manager.load_demandas()
        st.session_state.etapas = st.session_state.db_manager.load_etapas()
        st.session_state.reload_data = False
else:
    # Fallback to empty lists if DB not connected
    if "projetos" not in st.session_state:
        st.session_state.projetos = []
    if "demandas" not in st.session_state:
        st.session_state.demandas = []
    if "etapas" not in st.session_state:
        st.session_state.etapas = []

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def adicionar_projeto(nome: str, descricao: str, data_inicio: str, data_fim: str) -> bool:
    """Adiciona um novo projeto à lista e ao banco de dados."""
    try:
        novo_projeto = Projeto(
            id=f"proj_{len(st.session_state.projetos) + 1}",
            nome=nome,
            descricao=descricao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status="Ativo",
            responsavel="",
            orcamento=0.0
        )
        st.session_state.projetos.append(novo_projeto)
        
        # Salvar no Postgres se conectado
        if st.session_state.db_connected:
            st.session_state.db_manager.save_projetos(st.session_state.projetos)
        
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar projeto: {e}")
        return False

def editar_projeto(projeto_id: str, nome: str, descricao: str, data_inicio: str, data_fim: str) -> bool:
    """Edita um projeto existente."""
    try:
        for i, proj in enumerate(st.session_state.projetos):
            if proj.id == projeto_id:
                st.session_state.projetos[i] = Projeto(
                    id=projeto_id,
                    nome=nome,
                    descricao=descricao,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    status=proj.status,
                    responsavel=proj.responsavel,
                    orcamento=proj.orcamento
                )
                if st.session_state.db_connected:
                    st.session_state.db_manager.save_projetos(st.session_state.projetos)
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao editar projeto: {e}")
        return False

def deletar_projeto(projeto_id: str) -> bool:
    """Deleta um projeto."""
    try:
        st.session_state.projetos = [p for p in st.session_state.projetos if p.id != projeto_id]
        st.session_state.demandas = [d for d in st.session_state.demandas if d.projeto_id != projeto_id]
        
        if st.session_state.db_connected:
            st.session_state.db_manager.save_projetos(st.session_state.projetos)
            st.session_state.db_manager.save_demandas(st.session_state.demandas)
        
        return True
    except Exception as e:
        st.error(f"Erro ao deletar projeto: {e}")
        return False

def adicionar_demanda(projeto_id: str, titulo: str, descricao: str, prioridade: str, data_vencimento: str) -> bool:
    """Adiciona uma nova demanda."""
    try:
        nova_demanda = Demanda(
            id=f"dem_{len(st.session_state.demandas) + 1}",
            projeto_id=projeto_id,
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            status="Pendente",
            responsavel="",
            data_vencimento=data_vencimento,
            data_criacao=datetime.now().strftime("%Y-%m-%d"),
            horas_estimadas=0
        )
        st.session_state.demandas.append(nova_demanda)
        
        if st.session_state.db_connected:
            st.session_state.db_manager.save_demandas(st.session_state.demandas)
        
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar demanda: {e}")
        return False

def editar_demanda(demanda_id: str, titulo: str, descricao: str, prioridade: str, data_vencimento: str) -> bool:
    """Edita uma demanda existente."""
    try:
        for i, dem in enumerate(st.session_state.demandas):
            if dem.id == demanda_id:
                st.session_state.demandas[i] = Demanda(
                    id=demanda_id,
                    projeto_id=dem.projeto_id,
                    titulo=titulo,
                    descricao=descricao,
                    prioridade=prioridade,
                    status=dem.status,
                    responsavel=dem.responsavel,
                    data_vencimento=data_vencimento,
                    data_criacao=dem.data_criacao,
                    horas_estimadas=dem.horas_estimadas
                )
                if st.session_state.db_connected:
                    st.session_state.db_manager.save_demandas(st.session_state.demandas)
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao editar demanda: {e}")
        return False

def deletar_demanda(demanda_id: str) -> bool:
    """Deleta uma demanda."""
    try:
        st.session_state.demandas = [d for d in st.session_state.demandas if d.id != demanda_id]
        st.session_state.etapas = [e for e in st.session_state.etapas if e.demanda_id != demanda_id]
        
        if st.session_state.db_connected:
            st.session_state.db_manager.save_demandas(st.session_state.demandas)
            st.session_state.db_manager.save_etapas(st.session_state.etapas)
        
        return True
    except Exception as e:
        st.error(f"Erro ao deletar demanda: {e}")
        return False

def mudar_status_demanda(demanda_id: str, novo_status: str) -> bool:
    """Muda o status de uma demanda."""
    try:
        for i, dem in enumerate(st.session_state.demandas):
            if dem.id == demanda_id:
                st.session_state.demandas[i] = Demanda(
                    id=demanda_id,
                    projeto_id=dem.projeto_id,
                    titulo=dem.titulo,
                    descricao=dem.descricao,
                    prioridade=dem.prioridade,
                    status=novo_status,
                    responsavel=dem.responsavel,
                    data_vencimento=dem.data_vencimento,
                    data_criacao=dem.data_criacao,
                    horas_estimadas=dem.horas_estimadas
                )
                if st.session_state.db_connected:
                    st.session_state.db_manager.save_demandas(st.session_state.demandas)
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao mudar status: {e}")
        return False

def adicionar_etapa(demanda_id: str, titulo: str, descricao: str, data_vencimento: str) -> bool:
    """Adiciona uma nova etapa."""
    try:
        nova_etapa = Etapa(
            id=f"eta_{len(st.session_state.etapas) + 1}",
            demanda_id=demanda_id,
            titulo=titulo,
            descricao=descricao,
            status="Não Iniciada",
            responsavel="",
            data_vencimento=data_vencimento,
            data_criacao=datetime.now().strftime("%Y-%m-%d")
        )
        st.session_state.etapas.append(nova_etapa)
        
        if st.session_state.db_connected:
            st.session_state.db_manager.save_etapas(st.session_state.etapas)
        
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar etapa: {e}")
        return False

def deletar_etapa(etapa_id: str) -> bool:
    """Deleta uma etapa."""
    try:
        st.session_state.etapas = [e for e in st.session_state.etapas if e.id != etapa_id]
        
        if st.session_state.db_connected:
            st.session_state.db_manager.save_etapas(st.session_state.etapas)
        
        return True
    except Exception as e:
        st.error(f"Erro ao deletar etapa: {e}")
        return False

# ============================================================================
# MAIN UI
# ============================================================================

st.title("📊 Gestão de Demandas e Projetos")
st.markdown("---")

# Sidebar Navigation
with st.sidebar:
    st.header("⚙️ Configurações")
    st.markdown("### Dados")
    col1, col2 = st.columns(2)
    with col1:
        total_projetos = len(st.session_state.projetos)
        st.metric("Projetos", total_projetos)
    with col2:
        total_demandas = len(st.session_state.demandas)
        st.metric("Demandas", total_demandas)
    
    st.markdown("---")
    st.markdown("### Armazenamento")
    st.info("Dados armazenados em memória (sessão atual)")
    
    if st.button("🗑️ Limpar Tudo", key="clear_all"):
        st.session_state.projetos = []
        st.session_state.demandas = []
        st.session_state.etapas = []
        st.success("Todos os dados foram limpos!")
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "🎯 Kanban", "📋 Gerenciar", "⚙️ Configurações"])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================
with tab1:
    st.subheader("📈 Dashboard de Projetos")
    
    if st.session_state.projetos:
        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        demandas_pendentes = len([d for d in st.session_state.demandas if d.status == "Pendente"])
        demandas_em_progresso = len([d for d in st.session_state.demandas if d.status == "Em Progresso"])
        demandas_concluidas = len([d for d in st.session_state.demandas if d.status == "Concluído"])
        
        with col1:
            st.metric("Demandas Pendentes", demandas_pendentes)
        with col2:
            st.metric("Em Progresso", demandas_em_progresso)
        with col3:
            st.metric("Concluídas", demandas_concluidas)
        with col4:
            st.metric("Total", len(st.session_state.demandas))
        
        st.markdown("---")
        
        # Projects Display
        st.markdown("### 📌 Projetos Ativos")
        for projeto in st.session_state.projetos:
            with st.expander(f"📂 {projeto.nome}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Data Início:** {projeto.data_inicio}")
                with col2:
                    st.write(f"**Data Fim:** {projeto.data_fim}")
                with col3:
                    st.write(f"**Status:** {projeto.status}")
                
                st.write(f"**Descrição:** {projeto.descricao}")
                
                # Demandas deste projeto
                demandas_proj = [d for d in st.session_state.demandas if d.projeto_id == projeto.id]
                if demandas_proj:
                    st.write(f"**Demandas:** {len(demandas_proj)}")
                    for demanda in demandas_proj:
                        st.caption(f"• {demanda.titulo} ({demanda.status})")
                else:
                    st.info("Nenhuma demanda neste projeto")
    else:
        st.info("📌 Nenhum projeto cadastrado. Vá para 'Gerenciar' para criar um novo projeto.")

# ============================================================================
# TAB 2: KANBAN
# ============================================================================
with tab2:
    st.subheader("🎯 Visualização Kanban")
    
    if st.session_state.demandas:
        kanban = KanbanView(st.session_state.demandas)
        kanban.render()
    else:
        st.info("📌 Nenhuma demanda para visualizar. Crie uma demanda na aba 'Gerenciar'.")

# ============================================================================
# TAB 3: GERENCIAR
# ============================================================================
with tab3:
    st.subheader("📋 Gerenciar Projetos, Demandas e Etapas")
    
    subtab1, subtab2, subtab3 = st.tabs(["Projetos", "Demandas", "Etapas"])
    
    # ========================================================================
    # SUBTAB: PROJETOS
    # ========================================================================
    with subtab1:
        st.markdown("### ➕ Novo Projeto")
        
        col1, col2 = st.columns(2)
        with col1:
            nome_proj = st.text_input("Nome do Projeto", key="nome_proj_new")
        with col2:
            descricao_proj = st.text_area("Descrição", key="desc_proj_new", height=80)
        
        col1, col2 = st.columns(2)
        with col1:
            data_inicio_proj = st.date_input("Data de Início", key="data_ini_proj_new")
        with col2:
            data_fim_proj = st.date_input("Data de Fim", key="data_fim_proj_new")
        
        if st.button("✅ Criar Projeto", key="btn_criar_proj"):
            if nome_proj:
                if adicionar_projeto(nome_proj, descricao_proj, str(data_inicio_proj), str(data_fim_proj)):
                    st.success("✅ Projeto criado com sucesso!")
                    st.rerun()
            else:
                st.error("❌ Nome do projeto é obrigatório")
        
        st.markdown("---")
        st.markdown("### 📂 Projetos Existentes")
        
        if st.session_state.projetos:
            for projeto in st.session_state.projetos:
                with st.expander(f"📂 {projeto.nome}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {projeto.id}")
                        st.write(f"**Status:** {projeto.status}")
                        st.write(f"**Início:** {projeto.data_inicio}")
                    
                    with col2:
                        st.write(f"**Descrição:** {projeto.descricao}")
                        st.write(f"**Fim:** {projeto.data_fim}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✏️ Editar", key=f"edit_proj_{projeto.id}"):
                            st.session_state[f"edit_proj_{projeto.id}"] = True
                    
                    with col2:
                        if st.button("🗑️ Deletar", key=f"del_proj_{projeto.id}"):
                            if deletar_projeto(projeto.id):
                                st.success("✅ Projeto deletado!")
                                st.rerun()
                    
                    # Edit Form
                    if st.session_state.get(f"edit_proj_{projeto.id}", False):
                        st.markdown("#### Editar Projeto")
                        nome_edit = st.text_input("Nome", value=projeto.nome, key=f"nome_edit_{projeto.id}")
                        desc_edit = st.text_area("Descrição", value=projeto.descricao, key=f"desc_edit_{projeto.id}")
                        data_ini_edit = st.date_input("Data Início", value=pd.to_datetime(projeto.data_inicio), key=f"data_ini_edit_{projeto.id}")
                        data_fim_edit = st.date_input("Data Fim", value=pd.to_datetime(projeto.data_fim), key=f"data_fim_edit_{projeto.id}")
                        
                        if st.button("💾 Salvar", key=f"save_proj_{projeto.id}"):
                            if editar_projeto(projeto.id, nome_edit, desc_edit, str(data_ini_edit), str(data_fim_edit)):
                                st.success("✅ Projeto atualizado!")
                                st.session_state[f"edit_proj_{projeto.id}"] = False
                                st.rerun()
        else:
            st.info("Nenhum projeto cadastrado")
    
    # ========================================================================
    # SUBTAB: DEMANDAS
    # ========================================================================
    with subtab2:
        st.markdown("### ➕ Nova Demanda")
        
        projetos_options = [p.nome for p in st.session_state.projetos] if st.session_state.projetos else []
        
        if projetos_options:
            projeto_sel = st.selectbox("Selecione um Projeto", projetos_options, key="proj_sel_dem")
            projeto_id = next((p.id for p in st.session_state.projetos if p.nome == projeto_sel), None)
            
            titulo_dem = st.text_input("Título da Demanda", key="titulo_dem_new")
            descricao_dem = st.text_area("Descrição", key="desc_dem_new", height=80)
            
            col1, col2 = st.columns(2)
            with col1:
                prioridade_dem = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"], key="prior_dem_new")
            with col2:
                data_venc_dem = st.date_input("Data de Vencimento", key="data_venc_dem_new")
            
            if st.button("✅ Criar Demanda", key="btn_criar_dem"):
                if titulo_dem and projeto_id:
                    if adicionar_demanda(projeto_id, titulo_dem, descricao_dem, prioridade_dem, str(data_venc_dem)):
                        st.success("✅ Demanda criada com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Título e Projeto são obrigatórios")
        else:
            st.warning("⚠️ Crie um projeto primeiro")
        
        st.markdown("---")
        st.markdown("### 📋 Demandas Existentes")
        
        if st.session_state.demandas:
            for demanda in st.session_state.demandas:
                projeto_nome = next((p.nome for p in st.session_state.projetos if p.id == demanda.projeto_id), "Desconhecido")
                
                with st.expander(f"📋 {demanda.titulo} ({demanda.status})", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Projeto:** {projeto_nome}")
                        st.write(f"**Prioridade:** {demanda.prioridade}")
                        st.write(f"**Status:** {demanda.status}")
                    
                    with col2:
                        st.write(f"**Descrição:** {demanda.descricao}")
                        st.write(f"**Vencimento:** {demanda.data_vencimento}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        novo_status = st.selectbox("Novo Status", ["Pendente", "Em Progresso", "Concluído"], 
                                                  value=demanda.status, key=f"status_{demanda.id}")
                        if novo_status != demanda.status:
                            mudar_status_demanda(demanda.id, novo_status)
                            st.rerun()
                    
                    with col2:
                        if st.button("✏️ Editar", key=f"edit_dem_{demanda.id}"):
                            st.session_state[f"edit_dem_{demanda.id}"] = True
                    
                    with col3:
                        if st.button("🗑️ Deletar", key=f"del_dem_{demanda.id}"):
                            if deletar_demanda(demanda.id):
                                st.success("✅ Demanda deletada!")
                                st.rerun()
                    
                    # Edit Form
                    if st.session_state.get(f"edit_dem_{demanda.id}", False):
                        st.markdown("#### Editar Demanda")
                        titulo_edit = st.text_input("Título", value=demanda.titulo, key=f"titulo_edit_{demanda.id}")
                        desc_edit = st.text_area("Descrição", value=demanda.descricao, key=f"desc_edit_{demanda.id}")
                        prior_edit = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"], 
                                                 value=demanda.prioridade, key=f"prior_edit_{demanda.id}")
                        data_venc_edit = st.date_input("Data Vencimento", value=pd.to_datetime(demanda.data_vencimento), key=f"data_venc_edit_{demanda.id}")
                        
                        if st.button("💾 Salvar", key=f"save_dem_{demanda.id}"):
                            if editar_demanda(demanda.id, titulo_edit, desc_edit, prior_edit, str(data_venc_edit)):
                                st.success("✅ Demanda atualizada!")
                                st.session_state[f"edit_dem_{demanda.id}"] = False
                                st.rerun()
        else:
            st.info("Nenhuma demanda cadastrada")
    
    # ========================================================================
    # SUBTAB: ETAPAS
    # ========================================================================
    with subtab3:
        st.markdown("### ➕ Nova Etapa")
        
        demandas_options = [d.titulo for d in st.session_state.demandas] if st.session_state.demandas else []
        
        if demandas_options:
            demanda_sel = st.selectbox("Selecione uma Demanda", demandas_options, key="dem_sel_eta")
            demanda_id = next((d.id for d in st.session_state.demandas if d.titulo == demanda_sel), None)
            
            titulo_eta = st.text_input("Título da Etapa", key="titulo_eta_new")
            descricao_eta = st.text_area("Descrição", key="desc_eta_new", height=80)
            data_venc_eta = st.date_input("Data de Vencimento", key="data_venc_eta_new")
            
            if st.button("✅ Criar Etapa", key="btn_criar_eta"):
                if titulo_eta and demanda_id:
                    if adicionar_etapa(demanda_id, titulo_eta, descricao_eta, str(data_venc_eta)):
                        st.success("✅ Etapa criada com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Título e Demanda são obrigatórios")
        else:
            st.warning("⚠️ Crie uma demanda primeiro")
        
        st.markdown("---")
        st.markdown("### 📌 Etapas Existentes")
        
        if st.session_state.etapas:
            for etapa in st.session_state.etapas:
                demanda_titulo = next((d.titulo for d in st.session_state.demandas if d.id == etapa.demanda_id), "Desconhecida")
                
                with st.expander(f"📌 {etapa.titulo} ({etapa.status})", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Demanda:** {demanda_titulo}")
                        st.write(f"**Status:** {etapa.status}")
                    
                    with col2:
                        st.write(f"**Descrição:** {etapa.descricao}")
                        st.write(f"**Vencimento:** {etapa.data_vencimento}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✏️ Editar", key=f"edit_eta_{etapa.id}"):
                            st.session_state[f"edit_eta_{etapa.id}"] = True
                    
                    with col2:
                        if st.button("🗑️ Deletar", key=f"del_eta_{etapa.id}"):
                            if deletar_etapa(etapa.id):
                                st.success("✅ Etapa deletada!")
                                st.rerun()
        else:
            st.info("Nenhuma etapa cadastrada")

# ============================================================================
# TAB 4: CONFIGURAÇÕES
# ============================================================================
with tab4:
    st.subheader("⚙️ Configurações")
    
    st.markdown("### 💾 Armazenamento de Dados")
    
    if st.session_state.db_connected:
        st.success("✅ **Conectado ao PostgreSQL**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Host:** localhost:5432")
        with col2:
            st.info(f"**Database:** jones")
        with col3:
            st.info(f"**Driver:** pg8000")
        
        st.markdown("---")
        
        if st.button("🔄 Sincronizar com Banco de Dados", key="sync_db"):
            st.session_state.reload_data = True
            st.rerun()
    else:
        st.error("❌ **Erro de Conexão com PostgreSQL**")
        if st.session_state.get("db_error"):
            st.warning(f"Detalhes: {st.session_state.db_error}")
        st.info("Os dados estão sendo armazenados em memória (sessão atual).")
    
    st.markdown("---")
    st.markdown("### 📊 Informações da Sessão")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Projetos", len(st.session_state.projetos))
    with col2:
        st.metric("Demandas", len(st.session_state.demandas))
    with col3:
        st.metric("Etapas", len(st.session_state.etapas))
    
    st.markdown("---")
    st.markdown("### 🧹 Limpeza de Dados")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Limpar Dados em Memória", key="clear_memory"):
            st.session_state.projetos = []
            st.session_state.demandas = []
            st.session_state.etapas = []
            st.success("Dados em memória foram limpos!")
            st.rerun()
    
    with col2:
        if st.session_state.db_connected:
            if st.button("🗑️ Limpar Banco de Dados", key="clear_db"):
                try:
                    st.session_state.db_manager.clear_all()
                    st.session_state.projetos = []
                    st.session_state.demandas = []
                    st.session_state.etapas = []
                    st.success("✅ Todos os dados do banco foram limpos!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao limpar banco: {e}")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; margin-top: 2rem; color: #888;'>
    <small>App de Gestão de Demandas e Projetos | Versão 2.0</small>
</div>
""", unsafe_allow_html=True)
