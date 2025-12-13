import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from uuid import uuid4
from src.modules.models import Projeto, Demanda, Etapa, StatusEnum, PriorityEnum
from src.modules.postgres_manager import PostgresManager
from src.components.ui_components2 import create_demanda_form_v2, create_projeto_form, create_etapa_form
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

def _get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    try:
        secrets_url = st.secrets["DATABASE_URL"]
        if secrets_url:
            return secrets_url
    except Exception:
        pass
    return ""


def _get_secret_value(key: str) -> str:
    env_val = os.getenv(key)
    if env_val:
        return env_val
    try:
        secret_val = st.secrets[key]
        return str(secret_val) if secret_val is not None else ""
    except Exception:
        return ""


# Database URL (Postgres)
DATABASE_URL = _get_database_url()

# Initialize PostgresManager (apenas se houver DATABASE_URL)
if not DATABASE_URL:
    st.session_state.db_connected = False
    st.session_state.db_error = "DATABASE_URL não configurado. Defina em variáveis de ambiente ou em Secrets do Streamlit Cloud."
else:
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = PostgresManager(DATABASE_URL)

    # Test connection on startup
    if "db_connected" not in st.session_state:
        try:
            health = st.session_state.db_manager.health_check()
            # `health_check` returns a boolean; be defensive if an object returned
            if isinstance(health, bool):
                st.session_state.db_connected = health
            else:
                st.session_state.db_connected = bool(health.get("connected", False)) if isinstance(health, dict) else bool(health)
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

def adicionar_projeto(nome: str, descricao: str, data_criacao: str, data_conclusao: str) -> bool:
    """Adiciona um novo projeto à lista e ao banco de dados."""
    try:
        novo_projeto = Projeto(
            id=f"proj_{uuid4().hex}",
            nome=nome,
            descricao=descricao,
            data_criacao=data_criacao,
            data_conclusao=data_conclusao,
            status="Ativo",
            responsavel=""
        )
        st.session_state.projetos.append(novo_projeto)
        
        # Salvar no Postgres se conectado
        if st.session_state.db_connected:
            st.session_state.db_manager.save_projetos(st.session_state.projetos)
        
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar projeto: {e}")
        return False

def editar_projeto(projeto_id: str, nome: str, descricao: str, data_criacao: str, data_conclusao: str) -> bool:
    """Edita um projeto existente."""
    try:
        for i, proj in enumerate(st.session_state.projetos):
            if proj.id == projeto_id:
                st.session_state.projetos[i] = Projeto(
                    id=projeto_id,
                    nome=nome,
                    descricao=descricao,
                    data_criacao=data_criacao,
                    data_conclusao=data_conclusao,
                    status=proj.status,
                    responsavel=proj.responsavel
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
        demandas_para_remover = [d for d in st.session_state.demandas if d.projeto_id == projeto_id]

        st.session_state.projetos = [p for p in st.session_state.projetos if p.id != projeto_id]
        st.session_state.demandas = [d for d in st.session_state.demandas if d.projeto_id != projeto_id]

        if st.session_state.db_connected:
            # Remover dependências (demandas) e depois o projeto
            for d in demandas_para_remover:
                st.session_state.db_manager.delete_demanda(d.id)
            st.session_state.db_manager.delete_projeto(projeto_id)
        
        return True
    except Exception as e:
        st.error(f"Erro ao deletar projeto: {e}")
        return False

def adicionar_demanda_from_dict(data: dict) -> bool:
    """Adiciona nova demanda a partir de dict com campos completos."""
    try:
        new_id = data.get('id') or f"dem_{uuid4().hex}"
        nova_demanda = Demanda(
            id=new_id,
            titulo=data.get('titulo', ''),
            descricao=data.get('descricao', ''),
            projeto_id=data.get('projeto_id'),
            status=data.get('status', StatusEnum.TODO.value),
            prioridade=data.get('prioridade', PriorityEnum.MEDIA.value),
            etapa_id=data.get('etapa_id'),
            responsavel=data.get('responsavel'),
            data_inicio_plano=data.get('data_inicio_plano'),
            data_inicio_real=data.get('data_inicio_real'),
            data_vencimento_plano=data.get('data_vencimento_plano'),
            data_vencimento_real=data.get('data_vencimento_real'),
            data_vencimento=data.get('data_vencimento'),
            data_criacao=data.get('data_criacao') or datetime.now().strftime('%Y-%m-%d'),
            data_conclusao=data.get('data_conclusao'),
            percentual_completo=int(data.get('percentual_completo') or 0),
            tags=data.get('tags') or [],
            comentarios=data.get('comentarios') or []
        )
        st.session_state.demandas.append(nova_demanda)
        if st.session_state.db_connected:
            st.session_state.db_manager.save_demandas(st.session_state.demandas)
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar demanda: {e}")
        return False


def editar_demanda_from_dict(demanda_id: str, data: dict) -> bool:
    """Edita uma demanda usando um dict com campos completos."""
    try:
        for i, dem in enumerate(st.session_state.demandas):
            if dem.id == demanda_id:
                st.session_state.demandas[i] = Demanda(
                    id=demanda_id,
                    titulo=data.get('titulo', dem.titulo),
                    descricao=data.get('descricao', dem.descricao),
                    projeto_id=data.get('projeto_id', dem.projeto_id),
                    status=data.get('status', dem.status),
                    prioridade=data.get('prioridade', dem.prioridade),
                    etapa_id=data.get('etapa_id', dem.etapa_id),
                    responsavel=data.get('responsavel', dem.responsavel),
                    data_inicio_plano=data.get('data_inicio_plano', dem.data_inicio_plano),
                    data_inicio_real=data.get('data_inicio_real', dem.data_inicio_real),
                    data_vencimento_plano=data.get('data_vencimento_plano', dem.data_vencimento_plano),
                    data_vencimento_real=data.get('data_vencimento_real', dem.data_vencimento_real),
                    data_vencimento=data.get('data_vencimento', dem.data_vencimento),
                    data_criacao=data.get('data_criacao', dem.data_criacao),
                    data_conclusao=data.get('data_conclusao', dem.data_conclusao),
                    percentual_completo=int(data.get('percentual_completo', dem.percentual_completo or 0)),
                    tags=data.get('tags', dem.tags),
                    comentarios=data.get('comentarios', dem.comentarios)
                )
                if st.session_state.db_connected:
                    st.session_state.db_manager.save_demandas(st.session_state.demandas)
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao editar demanda: {e}")
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

        if st.session_state.db_connected:
            st.session_state.db_manager.delete_demanda(demanda_id)
        
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
    """Adiciona uma nova etapa e, opcionalmente, associa à demanda (via demanda.etapa_id)."""
    try:
        nova_etapa = Etapa(
            id=f"eta_{uuid4().hex}",
            nome=titulo,
            descricao=descricao,
            ordem=0,
            data_criacao=datetime.now().strftime("%Y-%m-%d")
        )
        st.session_state.etapas.append(nova_etapa)
        
        # associar etapa a demanda se informado
        if demanda_id:
            for i, d in enumerate(st.session_state.demandas):
                if d.id == demanda_id:
                    st.session_state.demandas[i].etapa_id = nova_etapa.id
                    break
        
        if st.session_state.db_connected:
            st.session_state.db_manager.save_etapas(st.session_state.etapas)
            st.session_state.db_manager.save_demandas(st.session_state.demandas)
        
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar etapa: {e}")
        return False

def deletar_etapa(etapa_id: str) -> bool:
    """Deleta uma etapa."""
    try:
        st.session_state.etapas = [e for e in st.session_state.etapas if e.id != etapa_id]
        # desassociar etapa de demandas que apontavam para ela
        for i, d in enumerate(st.session_state.demandas):
            if d.etapa_id == etapa_id:
                st.session_state.demandas[i].etapa_id = None

        if st.session_state.db_connected:
            st.session_state.db_manager.delete_etapa(etapa_id)
            st.session_state.db_manager.save_demandas(st.session_state.demandas)
        
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
    st.write('DB connected:', st.session_state.get('db_connected', False))
    if st.session_state.get('db_error'):
        st.write('DB error:', st.session_state.get('db_error'))
    
    if st.button("🗑️ Limpar Tudo", key="clear_all"):
        st.session_state.projetos = []
        st.session_state.demandas = []
        st.session_state.etapas = []
        st.success("Todos os dados foram limpos!")
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "🎯 Kanban", "⚙️ Configurações", "🛠️ Gerenciar"])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================
with tab1:
    st.subheader("📈 Dashboard de Projetos")
    
    # Render dashboard metrics and graphs
    from src.modules.kanban import DashboardMetrics
    DashboardMetrics.render_metrics(st.session_state.projetos, st.session_state.demandas)

    st.markdown("---")

    # Curva S (planejado x realizado)
    GanttChart.render_curva_s(st.session_state.demandas, st.session_state.projetos, st.session_state.etapas)

    # Gantt (visão completa com drilldown)
    st.markdown("### 📊 Gantt (Projetos / Etapas / Demandas)")
    GanttChart.render_gantt_com_drilldown(st.session_state.demandas, st.session_state.projetos, st.session_state.etapas)

# ============================================================================
# TAB 2: KANBAN
# ============================================================================
with tab2:
    st.subheader("🎯 Visualização Kanban")
    
    # Define callbacks
    def _on_status_change(demanda_obj, novo_status):
        try:
            mudar_status_demanda(demanda_obj.id, novo_status)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar status: {e}")
    
    def _on_edit(demanda_obj):
        # mantém o fluxo de edição dentro do Kanban (flag específica)
        st.session_state[f"kanban_edit_dem_{demanda_obj.id}"] = True
        st.rerun()
    
    def _on_delete(demanda_obj):
        try:
            deletar_demanda(demanda_obj.id)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao deletar demanda: {e}")
    
    if st.session_state.demandas:
        KanbanView.render_kanban(
            st.session_state.demandas,
            on_status_change=_on_status_change,
            on_edit=_on_edit,
            on_delete=_on_delete,
            projetos=st.session_state.projetos,
            etapas=st.session_state.etapas,
            on_edit_save=editar_demanda_from_dict
        )
    else:
        st.info("📌 Nenhuma demanda para visualizar.")

# ============================================================================
# TAB 3: CONFIGURAÇÕES
# ============================================================================
with tab3:
    st.subheader("⚙️ Configurações")
    
    st.markdown("### 💾 Armazenamento de Dados")
    
    if st.session_state.db_connected:
        st.success("✅ **Conectado ao PostgreSQL**")

        try:
            from sqlalchemy.engine.url import make_url
            url = make_url(st.session_state.db_manager.database_url)
            col1, col2, col3 = st.columns(3)
            with col1:
                host = url.host or ""
                port = url.port or ""
                st.info(f"**Host:** {host}:{port}".strip(':'))
            with col2:
                st.info(f"**Database:** {url.database or ''}")
            with col3:
                st.info(f"**Driver:** {url.drivername}")
        except Exception:
            # fallback simples, sem expor credenciais
            st.info("DB conectado (detalhes indisponíveis)")
        
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
# TAB 4: GERENCIAR (ADMIN)
# ============================================================================
with tab4:
    st.subheader("🛠️ Gerenciar (Cadastro)")

    if not st.session_state.get("db_connected", False):
        st.warning("Conecte o app ao PostgreSQL (DATABASE_URL) para cadastrar dados e persistir na nuvem.")
        st.stop()

    admin_password = _get_secret_value("ADMIN_PASSWORD")
    if not admin_password:
        st.warning(
            "A área de cadastro está protegida. Para habilitar, crie `ADMIN_PASSWORD` em Settings → Secrets (Streamlit Cloud)."
        )
        st.stop()

    if "admin_ok" not in st.session_state:
        st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        pwd = st.text_input("Senha de administrador", type="password", key="admin_pwd")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Entrar", key="admin_login"):
                st.session_state.admin_ok = pwd == admin_password
                if not st.session_state.admin_ok:
                    st.error("Senha inválida.")
                else:
                    st.rerun()
        st.stop()

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Sair", key="admin_logout"):
            st.session_state.admin_ok = False
            st.session_state.pop("admin_pwd", None)
            st.rerun()

    st.markdown("---")

    # -------------------- PROJETOS --------------------
    st.markdown("### 📁 Projetos")
    proj_mode = st.radio("Ação", ["Criar", "Editar"], horizontal=True, key="admin_proj_mode")

    if proj_mode == "Criar":
        proj_form = create_projeto_form(None)
        if st.button("Salvar Projeto", key="admin_proj_create"):
            novo = Projeto(
                id=f"proj_{uuid4().hex}",
                nome=proj_form.get("nome", ""),
                descricao=proj_form.get("descricao", ""),
                status=proj_form.get("status") or StatusEnum.TODO.value,
                responsavel=proj_form.get("responsavel") or "",
                data_criacao=datetime.now().strftime("%Y-%m-%d"),
                data_conclusao=proj_form.get("data_conclusao"),
            )
            st.session_state.projetos.append(novo)
            st.session_state.db_manager.save_projetos(st.session_state.projetos)
            st.success("Projeto criado.")
            st.rerun()
    else:
        if not st.session_state.projetos:
            st.info("Nenhum projeto cadastrado ainda.")
        else:
            proj_id = st.selectbox(
                "Selecione um projeto",
                options=[p.id for p in st.session_state.projetos],
                format_func=lambda x: next((p.nome for p in st.session_state.projetos if p.id == x), x),
                key="admin_proj_select",
            )
            projeto = next((p for p in st.session_state.projetos if p.id == proj_id), None)
            if projeto:
                proj_form = create_projeto_form(projeto)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Atualizar Projeto", key="admin_proj_update"):
                        for i, p in enumerate(st.session_state.projetos):
                            if p.id == projeto.id:
                                st.session_state.projetos[i] = Projeto(
                                    id=projeto.id,
                                    nome=proj_form.get("nome", projeto.nome),
                                    descricao=proj_form.get("descricao", projeto.descricao),
                                    status=proj_form.get("status", projeto.status),
                                    responsavel=proj_form.get("responsavel", projeto.responsavel),
                                    data_criacao=projeto.data_criacao,
                                    data_conclusao=proj_form.get("data_conclusao", projeto.data_conclusao),
                                )
                                break
                        st.session_state.db_manager.save_projetos(st.session_state.projetos)
                        st.success("Projeto atualizado.")
                        st.rerun()
                with c2:
                    if st.button("Excluir Projeto", key="admin_proj_delete"):
                        deletar_projeto(projeto.id)
                        st.success("Projeto excluído.")
                        st.rerun()

    st.markdown("---")

    # -------------------- ETAPAS --------------------
    st.markdown("### 🧩 Etapas")
    etapa_mode = st.radio("Ação", ["Criar", "Editar"], horizontal=True, key="admin_etapa_mode")
    if etapa_mode == "Criar":
        etapa_form = create_etapa_form(None)
        if st.button("Salvar Etapa", key="admin_etapa_create"):
            nova = Etapa(
                id=f"eta_{uuid4().hex}",
                nome=etapa_form.get("nome", ""),
                descricao=etapa_form.get("descricao", ""),
                ordem=int(etapa_form.get("ordem") or 0),
                data_criacao=datetime.now().strftime("%Y-%m-%d"),
            )
            st.session_state.etapas.append(nova)
            st.session_state.db_manager.save_etapas(st.session_state.etapas)
            st.success("Etapa criada.")
            st.rerun()
    else:
        if not st.session_state.etapas:
            st.info("Nenhuma etapa cadastrada ainda.")
        else:
            etapa_id = st.selectbox(
                "Selecione uma etapa",
                options=[e.id for e in st.session_state.etapas],
                format_func=lambda x: next((e.nome for e in st.session_state.etapas if e.id == x), x),
                key="admin_etapa_select",
            )
            etapa = next((e for e in st.session_state.etapas if e.id == etapa_id), None)
            if etapa:
                etapa_form = create_etapa_form(etapa)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Atualizar Etapa", key="admin_etapa_update"):
                        for i, e in enumerate(st.session_state.etapas):
                            if e.id == etapa.id:
                                st.session_state.etapas[i] = Etapa(
                                    id=etapa.id,
                                    nome=etapa_form.get("nome", etapa.nome),
                                    descricao=etapa_form.get("descricao", etapa.descricao),
                                    ordem=int(etapa_form.get("ordem", etapa.ordem) or 0),
                                    data_criacao=etapa.data_criacao,
                                )
                                break
                        st.session_state.db_manager.save_etapas(st.session_state.etapas)
                        st.success("Etapa atualizada.")
                        st.rerun()
                with c2:
                    if st.button("Excluir Etapa", key="admin_etapa_delete"):
                        deletar_etapa(etapa.id)
                        st.success("Etapa excluída.")
                        st.rerun()

    st.markdown("---")

    # -------------------- DEMANDAS --------------------
    st.markdown("### 📝 Demandas")
    if not st.session_state.projetos:
        st.warning("Crie pelo menos 1 projeto antes de cadastrar demandas.")
        st.stop()

    dem_mode = st.radio("Ação", ["Criar", "Editar"], horizontal=True, key="admin_dem_mode")
    if dem_mode == "Criar":
        data = create_demanda_form_v2(
            st.session_state.projetos,
            st.session_state.etapas,
            demanda=None,
            key_prefix="admin_new_dem",
        )
        if st.button("Salvar Demanda", key="admin_dem_create"):
            data["id"] = f"dem_{uuid4().hex}"
            if adicionar_demanda_from_dict(data):
                st.success("Demanda criada.")
                st.rerun()
    else:
        if not st.session_state.demandas:
            st.info("Nenhuma demanda cadastrada ainda.")
        else:
            dem_id = st.selectbox(
                "Selecione uma demanda",
                options=[d.id for d in st.session_state.demandas],
                format_func=lambda x: next((d.titulo for d in st.session_state.demandas if d.id == x), x),
                key="admin_dem_select",
            )
            demanda = next((d for d in st.session_state.demandas if d.id == dem_id), None)
            if demanda:
                data = create_demanda_form_v2(
                    st.session_state.projetos,
                    st.session_state.etapas,
                    demanda=demanda,
                    key_prefix=f"admin_edit_{demanda.id}",
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Atualizar Demanda", key="admin_dem_update"):
                        if editar_demanda_from_dict(demanda.id, data):
                            st.success("Demanda atualizada.")
                            st.rerun()
                with c2:
                    if st.button("Excluir Demanda", key="admin_dem_delete"):
                        if deletar_demanda(demanda.id):
                            st.success("Demanda excluída.")
                            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; margin-top: 2rem; color: #888;'>
    <small>App de Gestão de Demandas e Projetos | Versão 2.0</small>
</div>
""", unsafe_allow_html=True)
