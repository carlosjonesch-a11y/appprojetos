import streamlit as st
import plotly.graph_objects as go
from typing import List, Dict
from datetime import datetime, timedelta
from src.modules.models import Demanda, Projeto, Etapa
import pandas as pd


class GanttChart:
    """Classe para gerar gráficos de Gantt hierárquicos com drilldown"""
    
    @staticmethod
    def _parse_date(date_str):
        """Parse date string para datetime object (apenas data, sem hora)"""
        if not date_str:
            return datetime.now().date()
        
        try:
            if isinstance(date_str, str):
                # Remover 'Z' e timezone info
                date_str = date_str.replace('Z', '+00:00').split('+')[0]
                return datetime.fromisoformat(date_str).date()
            else:
                return date_str
        except:
            return datetime.now().date()
    
    @staticmethod
    def render_gantt_com_drilldown(
        demandas: List[Demanda],
        projetos: List[Projeto],
        etapas: List[Etapa]
    ):
        """Renderiza Gantt com drilldown: Projetos → Etapas → Demandas"""
        
        if not demandas:
            st.info("📊 Nenhuma demanda para exibir no Gantt")
            return
        
        # Inicializar session state para drilldown
        if 'gantt_level' not in st.session_state:
            st.session_state.gantt_level = 'projetos'
            st.session_state.selected_projeto = None
            st.session_state.selected_etapa = None
        
        # Layout com controles
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.session_state.gantt_level = st.radio(
                "📊 Nível de visualização",
                ["Projetos", "Etapas", "Demandas"],
                key="gantt_level_radio"
            ).lower()
        
        with col2:
            if st.session_state.gantt_level in ['etapas', 'demandas']:
                projeto_names = sorted(list(set([p.nome for p in projetos if any(d.projeto_id == p.id for d in demandas)])))
                projeto_options = ["🔄 Selecionar Tudo"] + projeto_names
                selected_proj_option = st.selectbox(
                    "🏗️ Projeto",
                    projeto_options,
                    key="gantt_select_projeto"
                )
                
                if selected_proj_option == "🔄 Selecionar Tudo":
                    st.session_state.selected_projeto = None
                else:
                    st.session_state.selected_projeto = selected_proj_option
            
            if st.session_state.gantt_level == 'demandas' and st.session_state.selected_projeto:
                # Filtrar etapas do projeto selecionado
                proj_id = next((p.id for p in projetos if p.nome == st.session_state.selected_projeto), None)
                etapas_do_proj = sorted(list(set([e.nome for e in etapas if any(d.etapa_id == e.id and d.projeto_id == proj_id for d in demandas)])))
                etapas_options = ["🔄 Selecionar Tudo"] + etapas_do_proj
                selected_etapa_option = st.selectbox(
                    "📋 Etapa",
                    etapas_options,
                    key="gantt_select_etapa"
                )
                
                if selected_etapa_option == "🔄 Selecionar Tudo":
                    st.session_state.selected_etapa = None
                else:
                    st.session_state.selected_etapa = selected_etapa_option
        
        with col3:
            if st.button("🔙 Voltar ao início", key="gantt_reset"):
                st.session_state.gantt_level = 'projetos'
                st.session_state.selected_projeto = None
                st.session_state.selected_etapa = None
                st.rerun()
        
        st.divider()
        
        # Renderizar baseado no nível
        if st.session_state.gantt_level == 'projetos':
            GanttChart._render_nivel_projetos(demandas, projetos, etapas)
        elif st.session_state.gantt_level == 'etapas':
            if st.session_state.selected_projeto:
                GanttChart._render_nivel_etapas(demandas, projetos, etapas, st.session_state.selected_projeto)
            else:
                GanttChart._render_nivel_projetos(demandas, projetos, etapas)
        elif st.session_state.gantt_level == 'demandas':
            if st.session_state.selected_projeto:
                if st.session_state.selected_etapa:
                    GanttChart._render_nivel_demandas(demandas, projetos, etapas, st.session_state.selected_projeto, st.session_state.selected_etapa)
                else:
                    GanttChart._render_todas_demandas_projeto(demandas, projetos, etapas, st.session_state.selected_projeto)
            else:
                GanttChart._render_nivel_projetos(demandas, projetos, etapas)
    
    @staticmethod
    def _render_nivel_projetos(demandas: List[Demanda], projetos: List[Projeto], etapas: List[Etapa]):
        """Renderiza visualização por Projetos"""
        st.subheader("📊 Gantt - Visão por Projetos")
        
        # Filtrar demandas com datas
        demandas_com_datas = [d for d in demandas if d.data_vencimento_plano]
        
        if not demandas_com_datas:
            st.error("⚠️ Nenhuma demanda com data preenchida")
            return
        
        # Agrupar por projeto
        projetos_map = {p.id: p.nome for p in projetos}
        tarefas = []
        
        # Calcular datas por projeto
        for proj_id in sorted(set(d.projeto_id for d in demandas_com_datas)):
            demandas_proj = [d for d in demandas_com_datas if d.projeto_id == proj_id]
            
            proj_nome = projetos_map.get(proj_id, "Sem Projeto")
            
            # Data mín/máx do projeto
            datas_inicio = [GanttChart._parse_date(d.data_inicio_plano or d.data_criacao) for d in demandas_proj]
            datas_fim = [GanttChart._parse_date(d.data_vencimento_plano) for d in demandas_proj]
            
            if datas_inicio and datas_fim:
                data_ini = min(datas_inicio)
                data_fim = max(datas_fim)
                num_demandas = len(demandas_proj)
                progresso = sum([d.percentual_completo or 0 for d in demandas_proj]) / len(demandas_proj) if demandas_proj else 0
                
                tarefas.append({
                    "Task": f"🏗️ {proj_nome}",
                    "Start": data_ini.isoformat(),
                    "End": data_fim.isoformat(),
                    "Demandas": num_demandas,
                    "Progresso": f"{progresso:.0f}%",
                    "Cor": "#667eea"
                })
        
        GanttChart._criar_gantt_simples(tarefas, "Projetos")
    
    @staticmethod
    def _render_nivel_etapas(demandas: List[Demanda], projetos: List[Projeto], etapas: List[Etapa], projeto_nome: str):
        """Renderiza visualização por Etapas de um projeto"""
        st.subheader(f"📋 Gantt - Etapas de {projeto_nome}")
        
        # Obter ID do projeto
        proj_id = next((p.id for p in projetos if p.nome == projeto_nome), None)
        if not proj_id:
            st.error("Projeto não encontrado")
            return
        
        # Filtrar demandas do projeto com datas
        demandas_proj = [d for d in demandas if d.projeto_id == proj_id and d.data_vencimento_plano]
        
        if not demandas_proj:
            st.error("⚠️ Nenhuma demanda neste projeto")
            return
        
        # Agrupar por etapa
        etapas_map = {e.id: e.nome for e in etapas}
        tarefas = []
        
        for etapa_id in sorted(set(d.etapa_id for d in demandas_proj if d.etapa_id)):
            demandas_etapa = [d for d in demandas_proj if d.etapa_id == etapa_id]
            
            etapa_nome = etapas_map.get(etapa_id, "Sem Etapa")
            
            datas_inicio = [GanttChart._parse_date(d.data_inicio_plano or d.data_criacao) for d in demandas_etapa]
            datas_fim = [GanttChart._parse_date(d.data_vencimento_plano) for d in demandas_etapa]
            
            if datas_inicio and datas_fim:
                data_ini = min(datas_inicio)
                data_fim = max(datas_fim)
                num_demandas = len(demandas_etapa)
                progresso = sum([d.percentual_completo or 0 for d in demandas_etapa]) / len(demandas_etapa) if demandas_etapa else 0
                
                tarefas.append({
                    "Task": f"  ├─ {etapa_nome}",
                    "Start": data_ini.isoformat(),
                    "End": data_fim.isoformat(),
                    "Demandas": num_demandas,
                    "Progresso": f"{progresso:.0f}%",
                    "Cor": "#764ba2"
                })
        
        GanttChart._criar_gantt_simples(tarefas, "Etapas")
    
    @staticmethod
    def _render_nivel_demandas(demandas: List[Demanda], projetos: List[Projeto], etapas: List[Etapa], projeto_nome: str, etapa_nome: str):
        """Renderiza visualização por Demandas"""
        st.subheader(f"✅ Gantt - Demandas: {etapa_nome} ({projeto_nome})")
        
        # Obter IDs
        proj_id = next((p.id for p in projetos if p.nome == projeto_nome), None)
        etapa_id = next((e.id for e in etapas if e.nome == etapa_nome), None)
        
        if not proj_id or not etapa_id:
            st.error("Projeto ou Etapa não encontrado")
            return
        
        # Filtrar demandas
        demandas_filtradas = [
            d for d in demandas 
            if d.projeto_id == proj_id and d.etapa_id == etapa_id and d.data_vencimento_plano
        ]
        
        if not demandas_filtradas:
            st.error("⚠️ Nenhuma demanda nesta etapa")
            return
        
        # Preparar tarefas
        tarefas = []
        
        for demanda in demandas_filtradas:
            data_ini = GanttChart._parse_date(demanda.data_inicio_plano or demanda.data_criacao)
            data_fim = GanttChart._parse_date(demanda.data_vencimento_plano)
            
            cores_status = {
                "A Fazer": "#FF6B6B",
                "Em Progresso": "#FFD93D",
                "Em Revisão": "#6BCB77",
                "Concluído": "#4D96FF"
            }
            
            tarefas.append({
                "Task": f"    ├─ {demanda.titulo}",
                "Start": data_ini.isoformat(),
                "End": data_fim.isoformat(),
                "Status": demanda.status,
                "Responsavel": demanda.responsavel or "Não atribuído",
                "Progresso": f"{demanda.percentual_completo or 0}%",
                "Cor": cores_status.get(demanda.status, "#999")
            })
        
        GanttChart._criar_gantt_detalhado(tarefas, "Demandas")
    
    @staticmethod
    def _render_todas_demandas_projeto(demandas: List[Demanda], projetos: List[Projeto], etapas: List[Etapa], projeto_nome: str):
        """Renderiza visualização de TODAS as demandas do projeto"""
        st.subheader(f"✅ Gantt - Todas as Demandas de {projeto_nome}")
        
        # Obter ID do projeto
        proj_id = next((p.id for p in projetos if p.nome == projeto_nome), None)
        if not proj_id:
            st.error("Projeto não encontrado")
            return
        
        # Filtrar demandas do projeto
        demandas_filtradas = [
            d for d in demandas 
            if d.projeto_id == proj_id and d.data_vencimento_plano
        ]
        
        if not demandas_filtradas:
            st.error("⚠️ Nenhuma demanda neste projeto")
            return
        
        # Preparar tarefas agrupadas por etapa
        tarefas = []
        etapas_map = {e.id: e.nome for e in etapas}
        
        # Agrupar por etapa
        for etapa_id in sorted(set(d.etapa_id for d in demandas_filtradas if d.etapa_id)):
            etapa_nome = etapas_map.get(etapa_id, "Sem Etapa")
            
            # Adicionar header de etapa
            demandas_etapa = [d for d in demandas_filtradas if d.etapa_id == etapa_id]
            
            for demanda in demandas_etapa:
                data_ini = GanttChart._parse_date(demanda.data_inicio_plano or demanda.data_criacao)
                data_fim = GanttChart._parse_date(demanda.data_vencimento_plano)
                
                cores_status = {
                    "A Fazer": "#FF6B6B",
                    "Em Progresso": "#FFD93D",
                    "Em Revisão": "#6BCB77",
                    "Concluído": "#4D96FF"
                }
                
                tarefas.append({
                    "Task": f"  ├─ {etapa_nome} → {demanda.titulo}",
                    "Start": data_ini.isoformat(),
                    "End": data_fim.isoformat(),
                    "Status": demanda.status,
                    "Responsavel": demanda.responsavel or "Não atribuído",
                    "Progresso": f"{demanda.percentual_completo or 0}%",
                    "Cor": cores_status.get(demanda.status, "#999")
                })
        
        GanttChart._criar_gantt_detalhado(tarefas, "Demandas")
    
    @staticmethod
    def _criar_gantt_simples(tarefas: List[Dict], nivel: str):
        """Cria gráfico Gantt simples com barras agregadas"""
        if not tarefas:
            st.warning("Nenhuma tarefa para exibir")
            return
        
        # Extrair datas
        todas_datas = []
        for tarefa in tarefas:
            todas_datas.append(pd.to_datetime(tarefa["Start"]).date())
            todas_datas.append(pd.to_datetime(tarefa["End"]).date())
        
        data_min = min(todas_datas)
        data_max = max(todas_datas)
        
        # Criar figura
        fig = go.Figure()
        
        # Adicionar barras
        for tarefa in tarefas:
            start = pd.to_datetime(tarefa["Start"]).date()
            end = pd.to_datetime(tarefa["End"]).date()
            duracao = (end - start).days + 1
            
            fig.add_trace(go.Scatter(
                x=[start, end],
                y=[tarefa["Task"], tarefa["Task"]],
                mode='lines',
                line=dict(color=tarefa["Cor"], width=25),
                name=tarefa["Task"],
                hovertext=f"""
                <b>{tarefa['Task'].strip()}</b><br>
                <b>Demandas:</b> {tarefa['Demandas']}<br>
                <b>Progresso:</b> {tarefa['Progresso']}<br>
                <b>Período:</b> {start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}<br>
                <b>Duração:</b> {duracao} dias
                """,
                hoverinfo='text',
                showlegend=False
            ))
            
            # Adicionar texto no meio
            meio_data = start + (end - start) / 2
            fig.add_annotation(
                x=meio_data,
                y=tarefa["Task"],
                text=f"{tarefa['Progresso']}",
                showarrow=False,
                font=dict(color='white', size=10, weight='bold'),
                bgcolor=tarefa["Cor"],
                bordercolor=tarefa["Cor"],
                borderwidth=0
            )
        
        # Configurar layout
        task_labels = [t["Task"] for t in tarefas]
        
        fig.update_layout(
            title=dict(
                text=f"<b>📊 Gantt - {nivel}</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=14)
            ),
            height=max(500, len(tarefas) * 60),
            xaxis_type='date',
            xaxis_title='Timeline',
            yaxis_title='',
            yaxis=dict(
                ticktext=task_labels,
                tickvals=task_labels,
                automargin=True,
                tickfont=dict(size=10)
            ),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='white',
            font=dict(size=11),
            margin=dict(l=250, r=50, t=100, b=50),
            hovermode='closest',
            showlegend=False
        )
        
        # Adicionar gridlines semanais
        current_date = data_min
        weekly_dates = []
        while current_date <= data_max:
            weekly_dates.append(current_date.isoformat())
            current_date += timedelta(days=7)
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            range=[data_min.isoformat(), data_max.isoformat()],
            tickvals=weekly_dates,
            tickformat='%d/%m'
        )
        
        # Linha de hoje
        hoje = datetime.now().date()
        if data_min <= hoje <= data_max:
            fig.add_shape(
                type="line",
                x0=hoje.isoformat(),
                y0=0,
                x1=hoje.isoformat(),
                y1=1,
                xref="x",
                yref="paper",
                line=dict(color="red", width=2, dash="dash")
            )
            fig.add_annotation(
                x=hoje.isoformat(),
                y=1,
                yref="paper",
                text="<b>Hoje</b>",
                showarrow=False,
                font=dict(color="red", size=10),
                yanchor="bottom"
            )
        
        fig.update_yaxes(showgrid=False)
        
        st.plotly_chart(fig, width="stretch", key=f"gantt_{nivel.lower()}")
    
    @staticmethod
    def _criar_gantt_detalhado(tarefas: List[Dict], nivel: str):
        """Cria gráfico Gantt detalhado com demandas individuais"""
        if not tarefas:
            st.warning("Nenhuma tarefa para exibir")
            return
        
        # Extrair datas
        todas_datas = []
        for tarefa in tarefas:
            todas_datas.append(pd.to_datetime(tarefa["Start"]).date())
            todas_datas.append(pd.to_datetime(tarefa["End"]).date())
        
        data_min = min(todas_datas)
        data_max = max(todas_datas)
        
        # Criar figura
        fig = go.Figure()
        
        # Adicionar barras
        for tarefa in tarefas:
            start = pd.to_datetime(tarefa["Start"]).date()
            end = pd.to_datetime(tarefa["End"]).date()
            duracao = (end - start).days + 1
            
            fig.add_trace(go.Scatter(
                x=[start, end],
                y=[tarefa["Task"], tarefa["Task"]],
                mode='lines',
                line=dict(color=tarefa["Cor"], width=20),
                name=tarefa["Task"],
                hovertext=f"""
                <b>{tarefa['Task'].strip()}</b><br>
                <b>Status:</b> {tarefa['Status']}<br>
                <b>Responsável:</b> {tarefa['Responsavel']}<br>
                <b>Progresso:</b> {tarefa['Progresso']}<br>
                <b>Período:</b> {start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}<br>
                <b>Duração:</b> {duracao} dias
                """,
                hoverinfo='text',
                showlegend=False
            ))
            
            # Adicionar texto no meio
            meio_data = start + (end - start) / 2
            fig.add_annotation(
                x=meio_data,
                y=tarefa["Task"],
                text=f"{tarefa['Progresso']}",
                showarrow=False,
                font=dict(color='white', size=9),
                bgcolor=tarefa["Cor"],
                bordercolor=tarefa["Cor"],
                borderwidth=0
            )
        
        # Configurar layout
        task_labels = [t["Task"] for t in tarefas]
        
        fig.update_layout(
            title=dict(
                text=f"<b>✅ Gantt - {nivel}</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=14)
            ),
            height=max(500, len(tarefas) * 50),
            xaxis_type='date',
            xaxis_title='Timeline',
            yaxis_title='',
            yaxis=dict(
                ticktext=task_labels,
                tickvals=task_labels,
                automargin=True,
                tickfont=dict(size=9)
            ),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='white',
            font=dict(size=10),
            margin=dict(l=300, r=50, t=100, b=50),
            hovermode='closest',
            showlegend=False
        )
        
        # Adicionar gridlines semanais
        current_date = data_min
        weekly_dates = []
        while current_date <= data_max:
            weekly_dates.append(current_date.isoformat())
            current_date += timedelta(days=7)
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            range=[data_min.isoformat(), data_max.isoformat()],
            tickvals=weekly_dates,
            tickformat='%d/%m'
        )
        
        # Linha de hoje
        hoje = datetime.now().date()
        if data_min <= hoje <= data_max:
            fig.add_shape(
                type="line",
                x0=hoje.isoformat(),
                y0=0,
                x1=hoje.isoformat(),
                y1=1,
                xref="x",
                yref="paper",
                line=dict(color="red", width=2, dash="dash")
            )
            fig.add_annotation(
                x=hoje.isoformat(),
                y=1,
                yref="paper",
                text="<b>Hoje</b>",
                showarrow=False,
                font=dict(color="red", size=10),
                yanchor="bottom"
            )
        
        fig.update_yaxes(showgrid=False)
        
        st.plotly_chart(fig, width="stretch", key=f"gantt_{nivel.lower()}_detalhado")
    
    # Manter compatibilidade com funções antigas
    @staticmethod
    def render_gantt_hierarquico(demandas: List[Demanda], projetos: List[Projeto], etapas: List[Etapa]):
        """Compatibilidade com nome antigo"""
        GanttChart.render_gantt_com_drilldown(demandas, projetos, etapas)
    
    @staticmethod
    def render_gantt_por_demanda(demandas: List[Demanda], projetos: List[Projeto], etapas: List[Etapa]):
        """Compatibilidade com nome antigo"""
        GanttChart.render_gantt_com_drilldown(demandas, projetos, etapas)
    
    @staticmethod
    def render_gantt_por_projeto(demandas: List[Demanda], projetos: List[Projeto], etapas: List[Etapa]):
        """Compatibilidade com nome antigo"""
        GanttChart.render_gantt_com_drilldown(demandas, projetos, etapas)
    
    @staticmethod
    def render_curva_s(
        demandas: List[Demanda],
        projetos: List[Projeto] = None,
        etapas: List[Etapa] = None
    ):
        """Renderiza gráfico de Curva S - Planejado vs Realizado"""
        
        if not demandas:
            st.info("📈 Nenhuma demanda para exibir na Curva S")
            return
        
        # Preparar dados de conclusão
        conclusoes_planejadas = []
        conclusoes_reais = []
        
        for demanda in demandas:
            # Data de conclusão planejada
            if demanda.data_vencimento_plano:
                data_plan = GanttChart._parse_date(demanda.data_vencimento_plano)
                conclusoes_planejadas.append(data_plan)
            
            # Data de conclusão real
            if demanda.data_vencimento_real:
                data_real = GanttChart._parse_date(demanda.data_vencimento_real)
                conclusoes_reais.append(data_real)
            elif demanda.status == "Concluído" and demanda.data_conclusao:
                data_real = GanttChart._parse_date(demanda.data_conclusao)
                conclusoes_reais.append(data_real)
        
        if not conclusoes_planejadas and not conclusoes_reais:
            st.warning("Nenhuma data de conclusão (planejada ou real) disponível")
            return
        
        # Contar acumuladas por data
        df_plan = None
        df_real = None
        
        if conclusoes_planejadas:
            df_plan = pd.DataFrame({
                'data': conclusoes_planejadas
            }).sort_values('data')
            df_plan['count'] = range(1, len(df_plan) + 1)
            df_plan.columns = ['Data', 'Acumulado']
        
        if conclusoes_reais:
            df_real = pd.DataFrame({
                'data': conclusoes_reais
            }).sort_values('data')
            df_real['count'] = range(1, len(df_real) + 1)
            df_real.columns = ['Data', 'Acumulado']
        
        # Criar figura
        fig = go.Figure()
        
        # Adicionar linha planejada
        if df_plan is not None:
            fig.add_trace(go.Scatter(
                x=df_plan['Data'],
                y=df_plan['Acumulado'],
                mode='lines+markers',
                name='Planejado',
                line=dict(color='#FFD93D', width=3),
                fill='tozeroy',
                fillcolor='rgba(255, 217, 61, 0.2)',
                hovertemplate='<b>Planejado</b><br>Data: %{x|%d/%m/%Y}<br>Acumulado: %{y} demandas<extra></extra>'
            ))
        
        # Adicionar linha real
        if df_real is not None:
            fig.add_trace(go.Scatter(
                x=df_real['Data'],
                y=df_real['Acumulado'],
                mode='lines+markers',
                name='Realizado',
                line=dict(color='#6BCB77', width=3),
                fill='tozeroy',
                fillcolor='rgba(107, 203, 119, 0.2)',
                hovertemplate='<b>Realizado</b><br>Data: %{x|%d/%m/%Y}<br>Acumulado: %{y} demandas<extra></extra>'
            ))
        
        # Configurar layout
        fig.update_layout(
            title=dict(
                text="<b>📈 Curva S - Planejado vs Realizado</b><br><sub>Acúmulo de demandas concluídas</sub>",
                x=0.5,
                xanchor='center'
            ),
            xaxis_title='Data de Conclusão',
            yaxis_title='Demandas Acumuladas',
            height=400,
            hovermode='x unified',
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='white',
            font=dict(size=11),
            margin=dict(l=60, r=50, t=100, b=50)
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        st.plotly_chart(fig, width="stretch", key="curva_s")
