import streamlit as st
from datetime import datetime
from typing import Optional, List, Callable
from src.modules.models import Demanda, StatusEnum, PriorityEnum


def create_projeto_card(projeto, col):
    with col:
        st.markdown(f"""
        <div style="
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: white;">{projeto.nome}</h4>
            <p style="margin: 5px 0; font-size: 0.9em;">{projeto.descricao[:100]}</p>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.85em;">
                <span>Status: <strong>{projeto.status}</strong></span>
                <span>Resp: <strong>{projeto.responsavel or 'Não atribuído'}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def create_demanda_card(demanda: Demanda, col, on_click_edit: Optional[Callable] = None, on_click_delete: Optional[Callable] = None):
    prioridade_cores = {"Baixa":"#4CAF50","Média":"#FF9800","Alta":"#f44336","Urgente":"#9C27B0"}
    status_cores = {"A Fazer":"#90CAF9","Em Progresso":"#FFB74D","Em Revisão":"#CE93D8","Concluído":"#81C784"}
    cor_prioridade = prioridade_cores.get(demanda.prioridade, "#999")
    cor_status = status_cores.get(demanda.status, "#999")
    with col:
        st.markdown(f"""
        <div style="border-left: 4px solid {cor_prioridade}; border-radius: 8px; padding: 15px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; cursor: pointer;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <h5 style="margin: 0 0 8px 0; color: #333;">{demanda.titulo}</h5>
                    <p style="margin: 0 0 8px 0; font-size: 0.85em; color: #666;">{demanda.descricao[:80]}</p>
                </div>
            </div>
            <div style="display: flex; gap: 8px; margin-top: 10px;">
                <span style="background: {cor_status}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">{demanda.status}</span>
                <span style="background: {cor_prioridade}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">{demanda.prioridade}</span>
            </div>
            <div style="display: flex; gap: 8px; margin-top: 10px; font-size: 0.75em; color: #999;">
                <span>📝 {demanda.responsavel or 'Não atribuído'}</span>
                <span>📅 {demanda.data_vencimento or 'Sem data'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Editar", key=f"edit_{demanda.id}"):
                if on_click_edit:
                    on_click_edit(demanda)
        with col2:
            if st.button("🗑️ Deletar", key=f"delete_{demanda.id}"):
                if on_click_delete:
                    on_click_delete(demanda)


def create_demanda_form_v2(projetos: List, etapas: List, demanda: Optional[Demanda] = None, key_prefix: Optional[str] = None):
    def _k(name: str):
        return f"{key_prefix}_{name}" if key_prefix else name
    st.subheader("📋 " + ("Editar Demanda" if demanda else "Nova Demanda"))
    col1, col2 = st.columns(2)
    with col1:
        titulo = st.text_input("Título", value=demanda.titulo if demanda else "", placeholder="Digite o título da demanda", key=_k("titulo"))
    with col2:
        projeto_id = st.selectbox("Projeto", options=[p.id for p in projetos], format_func=lambda x: next((p.nome for p in projetos if p.id == x), x), index=next((i for i, p in enumerate(projetos) if p.id == demanda.projeto_id), 0) if demanda else 0, key=_k("projeto"))
    descricao = st.text_area("Descrição", value=demanda.descricao if demanda else "", placeholder="Descreva a demanda em detalhes", height=100, key=_k("descricao"))
    col1, col2, col3 = st.columns(3)
    with col1:
        status = st.selectbox("Status", options=[s.value for s in StatusEnum], index=next((i for i, s in enumerate(StatusEnum) if s.value == (demanda.status if demanda else StatusEnum.TODO.value)), 0), key=_k("status"))
    with col2:
        prioridade = st.selectbox("Prioridade", options=[p.value for p in PriorityEnum], index=next((i for i, p in enumerate(PriorityEnum) if p.value == (demanda.prioridade if demanda else PriorityEnum.MEDIA.value)), 0), key=_k("prioridade"))
    with col3:
        etapa_id = st.selectbox("Etapa", options=[None] + [e.id for e in etapas], format_func=lambda x: "Sem etapa" if x is None else next((e.nome for e in etapas if e.id == x), x), key=_k("etapa"))
    col1, col2, col3 = st.columns(3)
    with col1:
        responsavel = st.text_input("Responsável", value=demanda.responsavel if demanda and demanda.responsavel else "", placeholder="Nome da pessoa responsável", key=_k("responsavel"))
    with col2:
        tags_input = st.text_input("Tags (separadas por vírgula)", value=", ".join(demanda.tags) if demanda and demanda.tags else "", placeholder="backend, urgente, api", key=_k("tags"))
    st.markdown("### 📅 Datas Planejadas")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio_plano = st.date_input("Data Início (Plano)", value=datetime.fromisoformat(demanda.data_inicio_plano).date() if demanda and demanda.data_inicio_plano else None, key=_k("ini_plano"))
    with col2:
        data_vencimento_plano = st.date_input("Data Vencimento (Plano)", value=datetime.fromisoformat(demanda.data_vencimento_plano).date() if demanda and demanda.data_vencimento_plano else None, key=_k("venc_plano"))
    st.markdown("### 📊 Datas Reais")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio_real = st.date_input("Data Início (Real)", value=datetime.fromisoformat(demanda.data_inicio_real).date() if demanda and demanda.data_inicio_real else None, key=_k("ini_real"))
    with col2:
        data_vencimento_real = st.date_input("Data Vencimento (Real)", value=datetime.fromisoformat(demanda.data_vencimento_real).date() if demanda and demanda.data_vencimento_real else None, key=_k("venc_real"))
    data_vencimento = data_vencimento_real if data_vencimento_real else data_vencimento_plano
    return {
        "titulo": titulo,
        "descricao": descricao,
        "projeto_id": projeto_id,
        "status": status,
        "prioridade": prioridade,
        "responsavel": responsavel,
        "etapa_id": etapa_id,
        "data_vencimento": data_vencimento.isoformat() if data_vencimento else None,
        "data_inicio_plano": data_inicio_plano.isoformat() if data_inicio_plano else None,
        "data_vencimento_plano": data_vencimento_plano.isoformat() if data_vencimento_plano else None,
        "data_inicio_real": data_inicio_real.isoformat() if data_inicio_real else None,
        "data_vencimento_real": data_vencimento_real.isoformat() if data_vencimento_real else None,
        "tags": [t.strip() for t in tags_input.split(",") if t.strip()]
    }


def create_projeto_form(projeto=None):
    """Cria um formulário para criar/editar projeto"""
    st.subheader("📊 " + ("Editar Projeto" if projeto else "Novo Projeto"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input(
            "Nome do Projeto",
            value=projeto.nome if projeto else "",
            placeholder="Digite o nome do projeto",
            key="form_proj_nome_input"
        )
    
    with col2:
        responsavel = st.text_input(
            "Responsável",
            value=projeto.responsavel if projeto and projeto.responsavel else "",
            placeholder="Nome do responsável",
            key="form_proj_responsavel_input"
        )
    
    descricao = st.text_area(
        "Descrição",
        value=projeto.descricao if projeto else "",
        placeholder="Descreva o projeto",
        height=100,
        key="form_proj_descricao_textarea"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        status = st.selectbox(
            "Status",
            options=[s.value for s in StatusEnum],
            index=next((i for i, s in enumerate(StatusEnum) if s.value == (projeto.status if projeto else StatusEnum.TODO.value)), 0),
            key="form_proj_status_selectbox"
        )
    
    with col2:
        data_conclusao = st.date_input(
            "Data de Conclusão Prevista",
            value=datetime.fromisoformat(projeto.data_conclusao).date() if projeto and projeto.data_conclusao else None,
            key="form_proj_data_conclusao_input"
        )
    
    return {
        "nome": nome,
        "descricao": descricao,
        "responsavel": responsavel,
        "status": status,
        "data_conclusao": data_conclusao.isoformat() if data_conclusao else None
    }


def create_etapa_form(etapa=None):
    st.subheader("🎯 " + ("Editar Etapa" if etapa else "Nova Etapa"))
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome da Etapa", value=etapa.nome if etapa else "", placeholder="Ex: Design, Desenvolvimento, Testes", key="form_etapa_nome_input")
    with col2:
        ordem = st.number_input("Ordem", value=etapa.ordem if etapa else 0, min_value=0, key="form_etapa_ordem_input")
    descricao = st.text_area("Descrição", value=etapa.descricao if etapa else "", placeholder="Descreva a etapa", height=80, key="form_etapa_descricao_textarea")
    return {"nome": nome, "descricao": descricao, "ordem": ordem}


def show_status_badge(status: str):
    status_cores = {"A Fazer": "#90CAF9", "Em Progresso": "#FFB74D", "Em Revisão": "#CE93D8", "Concluído": "#81C784"}
    cor = status_cores.get(status, "#999")
    st.markdown(f"""<span style="background: {cor}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{status}</span>""", unsafe_allow_html=True)


def show_priority_badge(prioridade: str):
    prioridade_cores = {"Baixa": "#4CAF50", "Média": "#FF9800", "Alta": "#f44336", "Urgente": "#9C27B0"}
    cor = prioridade_cores.get(prioridade, "#999")
    st.markdown(f"""<span style="background: {cor}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{prioridade}</span>""", unsafe_allow_html=True)

