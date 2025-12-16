import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from uuid import uuid4
import random
from src.modules.models import Projeto, Demanda, Etapa, StatusEnum, PriorityEnum
from src.modules.google_sheets_manager import GoogleSheetsManager, parse_spreadsheet_id, load_service_account_info_from_env_or_secrets
from src.components.ui_components2 import create_demanda_form_v2, create_projeto_form, create_etapa_form
from src.modules.kanban import KanbanView, DashboardMetrics
from src.modules.gantt import GanttChart
from src.modules.checklist import ChecklistView

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

def _get_gsheets_config() -> dict:
    spreadsheet_value = _get_secret_value("GSHEETS_SPREADSHEET_ID") or _get_secret_value("GSHEETS_URL")
    spreadsheet_id = parse_spreadsheet_id(spreadsheet_value)

    sa_configured = False
    try:
        _ = load_service_account_info_from_env_or_secrets(getattr(st, "secrets", None))
        sa_configured = True
    except Exception:
        sa_configured = False

    return {
        "spreadsheet_id": spreadsheet_id,
        "service_account_configured": sa_configured,
    }


def _gsheets_is_configured(cfg: dict) -> bool:
    return bool(cfg.get("spreadsheet_id")) and bool(cfg.get("service_account_configured"))


def _get_secret_value(key: str) -> str:
    env_val = os.getenv(key)
    if env_val:
        return env_val
    try:
        secret_val = st.secrets[key]
        return str(secret_val) if secret_val is not None else ""
    except Exception:
        return ""


def _parse_date_yyyy_mm_dd(value: str):
    if not value:
        return None
    try:
        # aceita "YYYY-MM-DD" ou ISO com hora
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def _planned_progress_for_demanda(d, today):
    start = _parse_date_yyyy_mm_dd(getattr(d, "data_inicio_plano", None))
    end = _parse_date_yyyy_mm_dd(getattr(d, "data_vencimento_plano", None))
    if not end:
        end = _parse_date_yyyy_mm_dd(getattr(d, "data_vencimento", None))

    if not start and not end:
        return None
    if not start and end:
        return 1.0 if today >= end else 0.0
    if start and not end:
        return 1.0 if today > start else 0.0

    if today <= start:
        return 0.0
    if today >= end:
        return 1.0
    total = (end - start).days
    if total <= 0:
        return 1.0
    return max(0.0, min(1.0, (today - start).days / float(total)))


def _actual_progress_for_demanda(d):
    try:
        pct = float(getattr(d, "percentual_completo", 0) or 0)
    except Exception:
        pct = 0.0
    return max(0.0, min(1.0, pct / 100.0))


def _compute_project_delay_risk(projetos, demandas):
    """Heurística baseada em Curva S: planejado vs realizado + prazos (projeto e demandas)."""
    today = datetime.now().date()
    rows = []

    for p in projetos:
        ds = [d for d in demandas if getattr(d, "projeto_id", None) == p.id]
        if not ds:
            continue

        # Prazo do projeto: preferir data_conclusao do projeto; senão usar maior vencimento planejado das demandas
        p_due = _parse_date_yyyy_mm_dd(getattr(p, "data_conclusao", None))
        if not p_due:
            due_candidates = [_parse_date_yyyy_mm_dd(getattr(d, "data_vencimento_plano", None)) for d in ds]
            due_candidates = [x for x in due_candidates if x]
            p_due = max(due_candidates) if due_candidates else None

        planned_list = []
        actual_list = []
        overdue_open = 0
        open_count = 0

        for d in ds:
            planned = _planned_progress_for_demanda(d, today)
            actual = _actual_progress_for_demanda(d)

            if planned is not None:
                planned_list.append(planned)
            actual_list.append(actual)

            is_open = getattr(d, "status", None) != StatusEnum.DONE.value and actual < 1.0
            if is_open:
                open_count += 1
                due = _parse_date_yyyy_mm_dd(getattr(d, "data_vencimento_plano", None))
                if not due:
                    due = _parse_date_yyyy_mm_dd(getattr(d, "data_vencimento", None))
                if due and due < today:
                    overdue_open += 1

        planned_pct = sum(planned_list) / len(planned_list) if planned_list else None
        actual_pct = sum(actual_list) / len(actual_list) if actual_list else 0.0
        slip = (planned_pct - actual_pct) if planned_pct is not None else 0.0

        # Projeção de término por velocidade (baseado em % realizado)
        start_candidates = [_parse_date_yyyy_mm_dd(getattr(d, "data_inicio_plano", None)) for d in ds]
        start_candidates = [x for x in start_candidates if x]
        p_start = min(start_candidates) if start_candidates else None

        projected_finish = None
        delay_days = None

        if p_start:
            elapsed_days = max(1, (today - p_start).days)
            velocity_per_day = actual_pct / float(elapsed_days)
            remaining = max(0.0, 1.0 - actual_pct)
            if velocity_per_day > 0.0:
                projected_finish = today + timedelta(days=int(round(remaining / velocity_per_day)))
                if p_due:
                    delay_days = max(0, (projected_finish - p_due).days)

        overdue_ratio = overdue_open / float(len(ds)) if ds else 0.0
        deadline_pressure = 0.0
        if p_due:
            days_to_due = (p_due - today).days
            if days_to_due <= 7:
                deadline_pressure = 0.15
            elif days_to_due <= 14:
                deadline_pressure = 0.08

        score = max(0.0, slip) * 0.7 + overdue_ratio * 0.3 + deadline_pressure

        if score >= 0.35 or (delay_days is not None and delay_days >= 1):
            risk_level = "Alto"
        elif score >= 0.18:
            risk_level = "Médio"
        else:
            risk_level = "Baixo"

        tendencia = "Atraso provável" if (delay_days is not None and delay_days >= 1) or risk_level == "Alto" else "No prazo"

        rows.append(
            {
                "projeto": getattr(p, "nome", p.id),
                "prazo_projeto": p_due.isoformat() if p_due else "",
                "pct_planejado_hoje": f"{int(round(planned_pct * 100))}%" if planned_pct is not None else "",
                "pct_real_hoje": f"{int(round(actual_pct * 100))}%",
                "gap_planejado_vs_real": f"{int(round(max(0.0, slip) * 100))}%" if planned_pct is not None else "",
                "demandas_abertas": open_count,
                "demandas_vencidas": overdue_open,
                "data_prevista_fim": projected_finish.isoformat() if projected_finish else "",
                "dias_previstos_atraso": int(delay_days) if delay_days is not None else None,
                "risco": risk_level,
                "tendência": tendencia,
                "_risk_score": float(score),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        # Garantir compatibilidade com Arrow (st.dataframe) evitando mistura str/int
        if "dias_previstos_atraso" in df.columns:
            df["dias_previstos_atraso"] = pd.to_numeric(df["dias_previstos_atraso"], errors="coerce").astype("Int64")
        df = df.sort_values(["tendência", "_risk_score", "dias_previstos_atraso", "demandas_vencidas"], ascending=[True, False, False, False])
        df = df.drop(columns=["_risk_score"], errors="ignore")
    return df



# Storage backend: Google Planilhas
gs_cfg = _get_gsheets_config()
use_gsheets = _gsheets_is_configured(gs_cfg)

if use_gsheets:
    st.session_state.storage_backend = "gsheets"
    if "db_manager" not in st.session_state or not isinstance(st.session_state.db_manager, GoogleSheetsManager):
        sa_info = load_service_account_info_from_env_or_secrets(getattr(st, "secrets", None))
        st.session_state.db_manager = GoogleSheetsManager(
            spreadsheet_id=gs_cfg["spreadsheet_id"],
            service_account_info=sa_info,
        )

    if "db_connected" not in st.session_state:
        try:
            st.session_state.db_connected = bool(st.session_state.db_manager.health_check())
        except Exception as e:
            st.session_state.db_connected = False
            st.session_state.db_error = str(e)
else:
    st.session_state.storage_backend = "none"
    st.session_state.db_connected = False
    st.session_state.db_error = (
        "Persistência não configurada. Configure Google Planilhas (GSHEETS_SPREADSHEET_ID + GOOGLE_SERVICE_ACCOUNT_JSON) em Secrets do Streamlit Cloud."
    )

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
    backend = st.session_state.get('storage_backend', 'none')
    if st.session_state.get('db_connected', False):
        st.info(f"Persistido em: {backend}")
    else:
        st.info("Dados em memória (sessão atual)")
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Dashboard", "🎯 Kanban", "⚙️ Configurações", "🛠️ Gerenciar", "✅ Check-list"])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================
with tab1:
    st.subheader("📈 Dashboard de Projetos")
    
    # Render dashboard metrics and graphs
    from src.modules.kanban import DashboardMetrics
    DashboardMetrics.render_metrics(st.session_state.projetos, st.session_state.demandas)

    # Previsão de atraso (Curva S: planejado vs realizado)
    st.markdown("---")
    st.markdown("### ⏱️ Previsão de Atraso (Curva S)")
    if st.session_state.projetos:
        df_risk = _compute_project_delay_risk(st.session_state.projetos, st.session_state.demandas)
        if df_risk.empty:
            st.info("Sem dados suficientes para calcular risco.")
        else:
            total = len(df_risk)
            likely_delay = int((df_risk["tendência"] == "Atraso provável").sum())
            st.metric("Projetos com atraso provável", f"{likely_delay}/{total}")
            st.dataframe(df_risk, use_container_width=True, hide_index=True)
    else:
        st.info("Cadastre projetos e demandas para ver a previsão.")

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
        # Filtros
        f1, f2 = st.columns(2)
        with f1:
            projeto_opt = st.selectbox(
                "Projeto",
                options=["Todos"] + [p.id for p in st.session_state.projetos],
                format_func=lambda x: "Todos" if x == "Todos" else next((p.nome for p in st.session_state.projetos if p.id == x), x),
                key="kanban_filter_projeto",
            )
        with f2:
            etapa_opt = st.selectbox(
                "Etapa",
                options=["Todas"] + [e.id for e in st.session_state.etapas],
                format_func=lambda x: "Todas" if x == "Todas" else next((e.nome for e in st.session_state.etapas if e.id == x), x),
                key="kanban_filter_etapa",
            )

        filtro_projeto = None if projeto_opt == "Todos" else projeto_opt
        filtro_etapa = None if etapa_opt == "Todas" else etapa_opt

        KanbanView.render_kanban(
            st.session_state.demandas,
            on_status_change=_on_status_change,
            on_edit=_on_edit,
            on_delete=_on_delete,
            filtro_projeto=filtro_projeto,
            filtro_etapa=filtro_etapa,
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

    storage_backend = st.session_state.get("storage_backend", "none")
    gs_cfg_view = _get_gsheets_config()
    gs_missing = []
    if not gs_cfg_view.get("spreadsheet_id"):
        gs_missing.append("GSHEETS_SPREADSHEET_ID")
    if not gs_cfg_view.get("service_account_configured"):
        gs_missing.append("GOOGLE_SERVICE_ACCOUNT_JSON")

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Backend selecionado:** {storage_backend}")
    with col_b:
        st.info(f"**Conectado:** {'sim' if st.session_state.get('db_connected') else 'não'}")

    if storage_backend == "gsheets":
        if st.session_state.get("db_connected"):
            st.success("✅ **Conectado ao Google Planilhas**")
        else:
            st.error("❌ **Falha ao conectar no Google Planilhas**")

        st.info(f"**Spreadsheet ID:** {gs_cfg_view.get('spreadsheet_id', '')}")

        if gs_missing:
            st.warning("Faltam secrets do Google: " + ", ".join(gs_missing))
            st.caption("Você pode usar GSHEETS_SPREADSHEET_ID (ou GSHEETS_URL) e GOOGLE_SERVICE_ACCOUNT_JSON.")

        if st.session_state.get("db_error"):
            st.warning(f"Detalhes: {st.session_state.db_error}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔌 Testar conexão Google Planilhas", key="test_gs"):
                try:
                    if gs_missing:
                        raise ValueError("Google Planilhas não configurado: faltam secrets: " + ", ".join(gs_missing))
                    sa_info = load_service_account_info_from_env_or_secrets(getattr(st, "secrets", None))
                    mgr = GoogleSheetsManager(
                        spreadsheet_id=gs_cfg_view["spreadsheet_id"],
                        service_account_info=sa_info,
                    )
                    ok = bool(mgr.health_check())
                    st.session_state.db_connected = ok
                    st.session_state.db_error = "" if ok else "Falha no health_check do Google Planilhas (sem detalhes adicionais)."
                    st.rerun()
                except Exception as e:
                    st.session_state.db_connected = False
                    st.session_state.db_error = str(e)
                    st.rerun()
        with col2:
            if st.button("🔄 Recarregar dados", key="reload_gs"):
                st.session_state.reload_data = True
                st.rerun()
    else:
        st.warning("Persistência não configurada (Google Planilhas).")
        if gs_missing:
            st.info("Faltam secrets: " + ", ".join(gs_missing))
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
        st.warning("Conecte o app ao Google Planilhas para cadastrar dados e persistir na nuvem.")
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

    # -------------------- DADOS FICTÍCIOS (DEMO) --------------------
    st.markdown("### 🧪 Dados fictícios (para teste)")

    def _seed_demo_data():
        pm = st.session_state.db_manager
        # limpar somente as tabelas core antes de popular
        pm.clear_core_data()

        rnd = random.Random(42)
        today = datetime.now().date()

        # Etapas
        etapas = [
            Etapa(id=f"eta_{uuid4().hex}", nome="Planejamento", descricao="", ordem=1, data_criacao=today.isoformat()),
            Etapa(id=f"eta_{uuid4().hex}", nome="Design", descricao="", ordem=2, data_criacao=today.isoformat()),
            Etapa(id=f"eta_{uuid4().hex}", nome="Desenvolvimento", descricao="", ordem=3, data_criacao=today.isoformat()),
            Etapa(id=f"eta_{uuid4().hex}", nome="Testes", descricao="", ordem=4, data_criacao=today.isoformat()),
            Etapa(id=f"eta_{uuid4().hex}", nome="Entrega", descricao="", ordem=5, data_criacao=today.isoformat()),
        ]

        # Projetos
        projetos = []
        for i in range(1, 21):
            start = today - timedelta(days=rnd.randint(10, 90))
            prazo = (today + timedelta(days=rnd.randint(15, 120))).isoformat()
            projetos.append(
                Projeto(
                    id=f"proj_{uuid4().hex}",
                    nome=f"Projeto Demo {i:02d}",
                    descricao=f"Projeto fictício para teste (seed).",
                    status="Ativo",
                    data_criacao=start.isoformat(),
                    data_conclusao=prazo,
                    responsavel="",
                )
            )

        # Demandas
        demandas = []
        status_choices = [StatusEnum.TODO.value, StatusEnum.IN_PROGRESS.value, StatusEnum.REVIEW.value, StatusEnum.DONE.value]
        prioridade_choices = [PriorityEnum.BAIXA.value, PriorityEnum.MEDIA.value, PriorityEnum.ALTA.value, PriorityEnum.URGENTE.value]

        for p_idx, p in enumerate(projetos):
            p_start = _parse_date_yyyy_mm_dd(getattr(p, "data_criacao", None)) or today
            p_due = _parse_date_yyyy_mm_dd(getattr(p, "data_conclusao", None)) or (today + timedelta(days=60))
            horizon_days = max(14, (p_due - p_start).days)

            # 5 demandas por projeto => 100 demandas (20 projetos)
            for j in range(1, 6):
                etapa = rnd.choice(etapas)
                prioridade = rnd.choice(prioridade_choices)

                # Datas planejadas dentro do horizonte do projeto
                start_offset = rnd.randint(0, max(0, horizon_days - 10))
                dur = rnd.randint(5, 25)
                start_plan = p_start + timedelta(days=start_offset)
                end_plan = start_plan + timedelta(days=dur)

                # Algumas demandas propositalmente vencidas (para aparecer risco no dashboard)
                if p_idx < 4 and j <= 2:
                    end_plan = today - timedelta(days=rnd.randint(1, 10))
                    start_plan = end_plan - timedelta(days=dur)

                # Progresso planejado vs realizado (Curva S simplificada)
                if today <= start_plan:
                    planned = 0.0
                elif today >= end_plan:
                    planned = 1.0
                else:
                    total = max(1, (end_plan - start_plan).days)
                    planned = max(0.0, min(1.0, (today - start_plan).days / float(total)))

                # Projetos iniciais ficam mais "atrasados" para evidenciar a previsão
                lag = 0.25 if p_idx < 4 else 0.05
                noise = rnd.uniform(-0.10, 0.10)
                actual = max(0.0, min(1.0, planned - lag + noise))

                # Distribuição de status coerente com %
                if actual >= 0.99:
                    dem_status = StatusEnum.DONE.value
                    actual = 1.0
                elif actual >= 0.70:
                    dem_status = StatusEnum.REVIEW.value
                elif actual >= 0.25:
                    dem_status = StatusEnum.IN_PROGRESS.value
                else:
                    dem_status = StatusEnum.TODO.value

                # Garante alguma variedade
                if rnd.random() < 0.08:
                    dem_status = rnd.choice(status_choices)

                concluida = dem_status == StatusEnum.DONE.value
                venc_real = end_plan if concluida else None
                data_conclusao = venc_real.isoformat() if venc_real else None

                demandas.append(
                    Demanda(
                        id=f"dem_{uuid4().hex}",
                        titulo=f"Demanda {j} - {p.nome}",
                        descricao="Tarefa fictícia para teste (seed).",
                        projeto_id=p.id,
                        status=dem_status,
                        prioridade=prioridade,
                        etapa_id=etapa.id,
                        responsavel="",
                        data_inicio_plano=start_plan.isoformat(),
                        data_inicio_real=None,
                        data_vencimento_plano=end_plan.isoformat(),
                        data_vencimento_real=venc_real.isoformat() if venc_real else None,
                        data_vencimento=end_plan.isoformat(),
                        data_criacao=p_start.isoformat(),
                        data_conclusao=data_conclusao,
                        percentual_completo=int(round(actual * 100)) if not concluida else 100,
                        tags=["seed"],
                        comentarios=[],
                    )
                )

        st.session_state.etapas = etapas
        st.session_state.projetos = projetos
        st.session_state.demandas = demandas

        pm.save_etapas(etapas)
        pm.save_projetos(projetos)
        pm.save_demandas(demandas)
        st.success("Dados fictícios inseridos no banco (20 projetos, 100 demandas, 5 etapas).")
        st.session_state.reload_data = True

    def _clear_demo_data():
        pm = st.session_state.db_manager
        pm.clear_core_data()
        st.session_state.projetos = []
        st.session_state.demandas = []
        st.session_state.etapas = []
        st.success("Tabelas de projetos/demandas/etapas limpas.")
        st.session_state.reload_data = True

    c1, c2 = st.columns(2)
    with c1:
        st.button("Popular banco com dados fictícios", key="seed_demo", on_click=_seed_demo_data)
    with c2:
        st.button("Deletar dados (projetos/demandas/etapas)", key="clear_demo", on_click=_clear_demo_data)

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
# TAB 5: CHECK-LIST (SEM PERSISTÊNCIA)
# ============================================================================
with tab5:
    ChecklistView.render()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; margin-top: 2rem; color: #888;'>
    <small>App de Gestão de Demandas e Projetos | Versão 2.0</small>
</div>
""", unsafe_allow_html=True)
