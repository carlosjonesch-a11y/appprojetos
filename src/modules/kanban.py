import streamlit as st
from typing import List, Optional, Callable
from src.modules.models import Demanda, StatusEnum

class KanbanView:
    """Classe para gerenciar visualização Kanban interativa"""
    
    @staticmethod
    def render_kanban(
        demandas: List[Demanda],
        on_status_change: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        filtro_projeto: Optional[str] = None,
        filtro_etapa: Optional[str] = None,
        filtro_responsavel: Optional[str] = None,
        projetos: Optional[List] = None,
        etapas: Optional[List] = None,
        on_edit_save: Optional[Callable] = None
    ):
        """
        Renderiza um kanban com colunas de status
        
        Args:
            demandas: Lista de demandas a exibir
            on_status_change: Callback para mudança de status
            on_edit: Callback para edição
            on_delete: Callback para deleção
            filtro_projeto: ID do projeto para filtrar
            filtro_responsavel: Nome do responsável para filtrar
        """
        
        # Filtra demandas
        demandas_filtradas = demandas
        if filtro_projeto:
            demandas_filtradas = [d for d in demandas_filtradas if d.projeto_id == filtro_projeto]
        if filtro_etapa:
            demandas_filtradas = [d for d in demandas_filtradas if getattr(d, 'etapa_id', None) == filtro_etapa]
        if filtro_responsavel:
            demandas_filtradas = [d for d in demandas_filtradas if d.responsavel == filtro_responsavel]
        
        # Agrupa demandas por status
        status_list = [s.value for s in StatusEnum]
        demandas_por_status = {status: [] for status in status_list}
        
        for demanda in demandas_filtradas:
            if demanda.status in demandas_por_status:
                demandas_por_status[demanda.status].append(demanda)
        
        # Ensure projetos / etapas available
        projetos = projetos or st.session_state.get('projetos', [])
        etapas = etapas or st.session_state.get('etapas', [])

        # Renderiza colunas
        cols = st.columns(len(status_list))
        
        for col_idx, (status, col) in enumerate(zip(status_list, cols)):
            with col:
                # Header da coluna
                demandas_nesta_coluna = demandas_por_status.get(status, [])
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    text-align: center;
                ">
                    <h4 style="margin: 0;">{status}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.8;">
                        {len(demandas_nesta_coluna)} demanda(s)
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Cards de demandas
                container = st.container()
                
                with container:
                    if not demandas_nesta_coluna:
                        st.info("Nenhuma demanda neste status")
                    else:
                        for i, demanda in enumerate(demandas_nesta_coluna):
                            KanbanView._render_demanda_card_kanban(
                                demanda,
                                i,
                                status,
                                on_status_change,
                                on_edit,
                                on_delete,
                                status_list,
                                projetos, etapas, on_edit_save
                            )
    
    @staticmethod
    def _render_demanda_card_kanban(
        demanda: Demanda,
        index: int,
        status_atual: str,
        on_status_change: Optional[Callable],
        on_edit: Optional[Callable],
        on_delete: Optional[Callable],
        status_list: List[str]
        , projetos: Optional[List] = None, etapas: Optional[List] = None, on_edit_save: Optional[Callable] = None):
        """Renderiza um card de demanda no kanban"""
        
        prioridade_cores = {
            "Baixa": "#4CAF50",
            "Média": "#FF9800",
            "Alta": "#f44336",
            "Urgente": "#9C27B0"
        }
        
        cor_prioridade = prioridade_cores.get(demanda.prioridade, "#999")
        
        # Card usando componentes do Streamlit
        with st.container(border=True):
            # Título e descrição
            st.markdown(f"**{demanda.titulo}**")
            st.caption(demanda.descricao[:50] if demanda.descricao else "Sem descrição")
            
            # Badges com prioridade e responsável
            col_badges = st.columns([1, 2])
            with col_badges[0]:
                st.markdown(f"🎯 **{demanda.prioridade}**")
            with col_badges[1]:
                if demanda.responsavel:
                    st.markdown(f"👤 {demanda.responsavel}")
            
            # Data de vencimento
            if demanda.data_vencimento:
                st.markdown(f"📅 **Vencimento:** {demanda.data_vencimento}")
            
            st.divider()
            
            # Botões de interação
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✏️ Editar", key=f"kanban_edit_{demanda.id}_{index}"):
                    # Open inline Kanban edit (set flag)
                    st.session_state[f"kanban_edit_dem_{demanda.id}"] = True
                    if on_edit:
                        on_edit(demanda)
                    st.rerun()
            
            with col2:
                # Dropdown para mudar status
                novo_status = st.selectbox(
                    "Novo status",
                    options=status_list,
                    index=status_list.index(demanda.status),
                    key=f"kanban_status_{demanda.id}_{index}",
                    label_visibility="collapsed"
                )
                
                if novo_status != demanda.status:
                    if st.button("✓ Atualizar", key=f"kanban_confirm_{demanda.id}_{index}"):
                        if on_status_change:
                            on_status_change(demanda, novo_status)
            
            with col3:
                if st.button("🗑️ Deletar", key=f"kanban_delete_{demanda.id}_{index}"):
                    if on_delete:
                        on_delete(demanda)

            # If flag set, render inline edit form
            # IMPORTANTE: o formulário usa st.columns internamente; por isso ele NÃO pode ficar dentro de um `with colX:`
            # (senão o Streamlit acusa nesting inválido de columns).
            if st.session_state.get(f"kanban_edit_dem_{demanda.id}", False):
                try:
                    from src.components.ui_components2 import create_demanda_form_v2

                    st.markdown("#### Editar Demanda")
                    projetos_list = projetos or st.session_state.get('projetos', [])
                    etapas_list = etapas or st.session_state.get('etapas', [])
                    form_data = create_demanda_form_v2(
                        projetos_list,
                        etapas_list,
                        demanda,
                        key_prefix=f"kanban_dem_{demanda.id}",
                    )

                    btn_save_col, btn_cancel_col = st.columns([1, 1])
                    with btn_save_col:
                        if st.button("💾 Salvar", key=f"kanban_save_{demanda.id}_{index}"):
                            if on_edit_save:
                                on_edit_save(demanda.id, form_data)
                            st.session_state[f"kanban_edit_dem_{demanda.id}"] = False
                            st.rerun()
                    with btn_cancel_col:
                        if st.button("✖️ Cancelar", key=f"kanban_cancel_{demanda.id}_{index}"):
                            st.session_state[f"kanban_edit_dem_{demanda.id}"] = False
                            st.rerun()
                except Exception as err:
                    st.error(f"Erro ao exibir o formulário de edição no Kanban: {err}")

class DashboardMetrics:
    """Classe para exibir métricas do dashboard"""
    
    @staticmethod
    def render_metrics(projetos: List, demandas: List[Demanda]):
        """Renderiza métricas resumidas"""
        
        st.markdown("---")
        st.subheader("📊 Métricas do Dashboard")
        
        # Calcula métricas
        total_projetos = len(projetos)
        total_demandas = len(demandas)
        demandas_concluidas = len([d for d in demandas if d.status == "Concluído"])
        demandas_urgentes = len([d for d in demandas if d.prioridade == "Urgente"])
        demandas_em_progresso = len([d for d in demandas if d.status == "Em Progresso"])
        taxa_conclusao = (demandas_concluidas / total_demandas * 100) if total_demandas > 0 else 0
        
        # Exibe métricas em cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Projetos", total_projetos, delta=None)
        
        with col2:
            st.metric("Total de Demandas", total_demandas, delta=None)
        
        with col3:
            st.metric("Demandas Concluídas", demandas_concluidas, delta=f"{taxa_conclusao:.1f}%")
        
        with col4:
            st.metric("⚠️ Urgentes", demandas_urgentes, delta="crítico" if demandas_urgentes > 0 else "ok")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de status
            status_counts = {}
            for d in demandas:
                status_counts[d.status] = status_counts.get(d.status, 0) + 1
            
            if status_counts:
                st.bar_chart(status_counts)
                st.caption("Demandas por Status")
        
        with col2:
            # Gráfico de prioridade
            prioridade_counts = {}
            for d in demandas:
                prioridade_counts[d.prioridade] = prioridade_counts.get(d.prioridade, 0) + 1
            
            if prioridade_counts:
                st.bar_chart(prioridade_counts)
                st.caption("Demandas por Prioridade")
