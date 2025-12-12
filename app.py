import streamlit as st
import uuid
import json
from datetime import datetime
import os
from src.modules.models import Projeto, Demanda, Etapa, StatusEnum, PriorityEnum
from src.modules.google_sheets_manager import GoogleSheetsManager
from src.modules.postgres_manager import PostgresManager
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

# Inicialização do Google Sheets Manager / Storage Backend (PRIMEIRO)
# Define um backend padrão se ainda não especificado
if "storage_backend" not in st.session_state:
    st.session_state.storage_backend = st.session_state.get('storage_backend', 'local')
if "google_sheets_manager" not in st.session_state:
    try:
        # Prefer Postgres if configured in secrets (DATABASE_URL)
        db_url = None
        if "DATABASE_URL" in st.secrets:
            db_url = st.secrets["DATABASE_URL"]
        elif os.environ.get('DATABASE_URL'):
            db_url = os.environ.get('DATABASE_URL')
        if db_url:
            try:
                pgm = PostgresManager(db_url)
                if pgm.connected:
                    st.session_state.google_sheets_manager = pgm
                    st.info("✅ Conectado via PostgreSQL (storage)")
                    # Skip other credential checks
                    st.session_state.storage_backend = 'postgres'
            except Exception as e:
                print(f"DEBUG: Falha ao conectar PostgreSQL: {e}")
                st.session_state.google_sheets_manager = None
        # If no Postgres or failed, fall back to other methods
        if not st.session_state.get('google_sheets_manager'):
        secrets_creds = None
        
        # 1. Tenta chave específica GOOGLE_CREDENTIALS
        if "GOOGLE_CREDENTIALS" in st.secrets:
            secrets_creds = st.secrets["GOOGLE_CREDENTIALS"]
            print(f"DEBUG: Encontrado GOOGLE_CREDENTIALS em secrets. Tipo: {type(secrets_creds)}")
            
        # 2. Tenta verificar se as secrets são as próprias credenciais (estrutura plana)
        # Isso acontece se o usuário colar o conteúdo do JSON direto no editor de secrets
        elif "type" in st.secrets and st.secrets["type"] == "service_account":
            secrets_creds = dict(st.secrets)
            print("DEBUG: Encontrada estrutura plana de service_account em secrets")

        if secrets_creds:
            # Se for string JSON, converte para dict
            if isinstance(secrets_creds, str):
                secrets_creds = secrets_creds.strip()
                if secrets_creds.startswith("{"):
                    try:
                        secrets_creds = json.loads(secrets_creds)
                    except Exception as e:
                        print(f"DEBUG: Erro ao fazer parse do JSON: {e}")
                        # Deixa como string se falhar, pode ser um caminho
            
            # Se for objeto de secrets, converte para dict
            if hasattr(secrets_creds, "to_dict"):
                secrets_creds = secrets_creds.to_dict()
            elif not isinstance(secrets_creds, (dict, str)):
                try:
                    secrets_creds = dict(secrets_creds)
                except:
                    pass

            manager = GoogleSheetsManager(secrets_creds)
            if manager.connected:
                st.session_state.google_sheets_manager = manager
                st.session_state.storage_backend = 'google'
                st.info("✅ Conectado via Streamlit Secrets")
            else:
                st.session_state.google_sheets_manager = None
        
        # Se não houver secrets, tenta arquivo local (desenvolvimento)
        elif os.path.exists("credentials.json"):
            manager = GoogleSheetsManager("credentials.json")
            if manager.connected:
                st.session_state.google_sheets_manager = manager
                st.session_state.storage_backend = 'google'
                st.info("✅ Conectado via credentials.json local")
            else:
                st.session_state.google_sheets_manager = None
        else:
            st.session_state.google_sheets_manager = None
            # Default to local storage when no cloud backend is available
            st.session_state.storage_backend = st.session_state.get('storage_backend', 'local')
            # Log para ajudar no debug
            print("DEBUG: Nenhuma credencial encontrada em st.secrets ou credentials.json")
            print(f"DEBUG: Chaves disponíveis em st.secrets: {list(st.secrets.keys())}")
            st.warning("⚠️ Credenciais não encontradas. Configure as secrets no Streamlit Cloud.")
            
            # DEBUG VISUAL TEMPORÁRIO (Remover em produção)
            with st.expander("🕵️ Debug de Credenciais (Seu app não está conectando)"):
                st.write("Verificando secrets...")
                if "GOOGLE_CREDENTIALS" in st.secrets:
                    st.success("Chave 'GOOGLE_CREDENTIALS' encontrada!")
                    creds = st.secrets["GOOGLE_CREDENTIALS"]
                    st.write(f"Tipo: {type(creds)}")
                    if isinstance(creds, dict) or hasattr(creds, "keys"):
                        st.write(f"Chaves: {list(creds.keys())}")
                        if "private_key" in creds:
                            pk = creds["private_key"]
                            st.write(f"Private Key começa com: {pk[:20]}...")
                            st.write(f"Tem quebra de linha real? {'Sim' if '\n' in pk else 'Não'}")
                            st.write(f"Tem barra-n literal? {'Sim' if '\\n' in pk else 'Não'}")
                elif "type" in st.secrets and st.secrets["type"] == "service_account":
                    st.success("Estrutura plana encontrada!")
                else:
                    st.error("Nenhuma chave válida encontrada em st.secrets")
                    st.write("Chaves disponíveis:", list(st.secrets.keys()))

    except Exception as e:
        st.session_state.google_sheets_manager = None
        st.error(f"⚠️ Erro ao conectar Google Sheets: {str(e)}")
        # Debug info
        st.write(f"Tipo do erro: {type(e)}")
        import traceback
        st.code(traceback.format_exc())

# Inicialização de estado - carrega do Google Sheets se disponível
if "projetos" not in st.session_state:
    if st.session_state.google_sheets_manager:
        try:
            st.session_state.projetos = st.session_state.google_sheets_manager.load_projetos()
        except:
            st.session_state.projetos = []
    else:
        st.session_state.projetos = []

if "demandas" not in st.session_state:
    if st.session_state.google_sheets_manager:
        try:
            st.session_state.demandas = st.session_state.google_sheets_manager.load_demandas()
        except:
            st.session_state.demandas = []
    else:
        st.session_state.demandas = []

if "etapas" not in st.session_state:
    if st.session_state.google_sheets_manager:
        try:
            st.session_state.etapas = st.session_state.google_sheets_manager.load_etapas()
        except:
            st.session_state.etapas = []
    else:
        st.session_state.etapas = []

if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = False

if "demanda_em_edicao" not in st.session_state:
    st.session_state.demanda_em_edicao = None

if "projeto_em_edicao" not in st.session_state:
    st.session_state.projeto_em_edicao = None

# ============= FUNÇÕES AUXILIARES =============

def carregar_dados():
    """Carrega dados do backend selecionado"""
    backend = st.session_state.get('storage_backend', 'local')
    if backend == 'local':
        st.info("Usando armazenamento local. Nenhuma sincronização remota realizada.")
        return

    mgr = st.session_state.get('google_sheets_manager')
    if not mgr:
        st.error("Nenhum gerenciador de backend disponível para carregar dados.")
        return

    try:
        with st.spinner("Carregando dados..."):
            st.session_state.projetos = mgr.load_projetos()
            st.session_state.demandas = mgr.load_demandas()
            st.session_state.etapas = mgr.load_etapas()
        st.success("Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

def salvar_dados():
    """Salva dados no backend selecionado"""
    backend = st.session_state.get('storage_backend', 'local')
    if backend == 'local':
        st.info("Dados mantidos apenas localmente (sem sincronização remota).")
        return

    mgr = st.session_state.get('google_sheets_manager')
    if not mgr:
        st.error("Nenhum gerenciador de backend disponível para salvar dados.")
        return

    try:
        with st.spinner("Salvando dados..."):
            mgr.save_projetos(st.session_state.projetos)
            mgr.save_demandas(st.session_state.demandas)
            mgr.save_etapas(st.session_state.etapas)
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
    # Remove locally
    st.session_state.projetos = [p for p in st.session_state.projetos if p.id != projeto_id]
    st.session_state.demandas = [d for d in st.session_state.demandas if d.projeto_id != projeto_id]
    # If using Postgres backend, delete from DB as well
    if st.session_state.get('storage_backend') == 'postgres' and st.session_state.get('google_sheets_manager'):
        try:
            deleted = st.session_state.google_sheets_manager.delete_projeto(projeto_id)
            if deleted:
                st.info('Projeto excluído do banco Postgres')
        except Exception as e:
            st.warning(f'Falha ao excluir do Postgres: {str(e)}')
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
    if st.session_state.get('storage_backend') == 'postgres' and st.session_state.get('google_sheets_manager'):
        try:
            deleted = st.session_state.google_sheets_manager.delete_demanda(demanda_id)
            if deleted:
                st.info('Demanda excluída do banco Postgres')
        except Exception as e:
            st.warning(f'Falha ao excluir demanda do Postgres: {str(e)}')
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
    if st.session_state.get('storage_backend') == 'postgres' and st.session_state.get('google_sheets_manager'):
        try:
            deleted = st.session_state.google_sheets_manager.delete_etapa(etapa_id)
            if deleted:
                st.info('Etapa excluída do banco Postgres')
        except Exception as e:
            st.warning(f'Falha ao excluir etapa do Postgres: {str(e)}')
    salvar_dados()
    st.success("Etapa deletada com sucesso!")

# ============= INTERFACE PRINCIPAL =============

# Header
col1, col2 = st.columns([3, 1])

with col1:
    st.title("📊 Gestão de Demandas de Projeto")
    st.markdown("*Organize suas demandas com eficiência e rastreie o progresso em tempo real*")

with col2:
    if st.button("🔄 Sincronizar"):
        carregar_dados()
    # Mostrar backend atual
    storage_backend = st.session_state.get('storage_backend', 'local')
    st.caption(f"Backend atual: {storage_backend}")

storage_backend = st.session_state.get('storage_backend', 'local')

if storage_backend == 'google' and not st.session_state.get('google_sheets_manager'):
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

    # DEBUG VISUAL (Movido para cá para garantir visibilidade)
    with st.expander("🕵️ Debug de Credenciais (Clique aqui se não conecta)"):
        st.write("### Diagnóstico de Secrets")
        
        # Versões das bibliotecas
        import pyasn1
        import rsa
        st.write(f"**Versão pyasn1:** `{pyasn1.__version__}` (Esperado: 0.5.1)")
        st.write(f"**Versão rsa:** `{rsa.__version__}`")
        
        # Verifica GOOGLE_CREDENTIALS
        if "GOOGLE_CREDENTIALS" in st.secrets:
            st.success("✅ Chave 'GOOGLE_CREDENTIALS' encontrada em st.secrets")
            creds = st.secrets["GOOGLE_CREDENTIALS"]
            st.write(f"**Tipo:** `{type(creds)}`")
            
            if isinstance(creds, dict) or hasattr(creds, "keys"):
                st.write(f"**Chaves disponíveis:** `{list(creds.keys())}`")
                if "private_key" in creds:
                    pk = creds["private_key"]
                    st.write(f"**Private Key (início):** `{pk[:25]}...`")
                    st.write(f"**Contém quebra de linha real (\\n)?** {'✅ Sim' if '\n' in pk else '❌ Não'}")
                    st.write(f"**Contém literal string (\\\\n)?** {'⚠️ Sim' if '\\n' in pk else '✅ Não'}")
            elif isinstance(creds, str):
                st.write("**Conteúdo é uma string.** Tentando parse JSON...")
                try:
                    import json
                    parsed = json.loads(creds)
                    st.success("✅ JSON válido!")
                    st.write(f"**Chaves no JSON:** `{list(parsed.keys())}`")
                except Exception as e:
                    st.error(f"❌ Erro ao ler JSON: {e}")
        
        # Verifica estrutura plana
        elif "type" in st.secrets and st.secrets["type"] == "service_account":
            st.success("✅ Estrutura plana (TOML) detectada!")
            st.write(f"**Chaves disponíveis:** `{list(st.secrets.keys())}`")
            if "private_key" in st.secrets:
                pk = st.secrets["private_key"]
                st.write(f"**Private Key (início):** `{pk[:25]}...`")
                st.write(f"**Contém quebra de linha real (\\n)?** {'✅ Sim' if '\n' in pk else '❌ Não'}")
        
        else:
            st.error("❌ Nenhuma credencial encontrada em st.secrets")
            st.write("Chaves disponíveis:", list(st.secrets.keys()))
        
        # Verifica se houve erro na tentativa de conexão
        if st.session_state.get("google_sheets_manager") is None:
             # Tenta instanciar temporariamente para pegar o erro
             try:
                 if "GOOGLE_CREDENTIALS" in st.secrets:
                     tmp_creds = st.secrets["GOOGLE_CREDENTIALS"]
                 elif "type" in st.secrets and st.secrets["type"] == "service_account":
                     tmp_creds = dict(st.secrets)
                 else:
                     tmp_creds = None
                 
                 if tmp_creds:
                     # Conversão rápida igual ao código principal
                     if hasattr(tmp_creds, "to_dict"): tmp_creds = tmp_creds.to_dict()
                     elif not isinstance(tmp_creds, (dict, str)): tmp_creds = dict(tmp_creds)
                     
                     tmp_manager = GoogleSheetsManager(tmp_creds)
                     if not tmp_manager.connected:
                         st.error(f"❌ Erro retornado pelo Google Sheets: {tmp_manager.last_error}")
                         if tmp_manager.error_traceback:
                             st.code(tmp_manager.error_traceback, language="python")
                         
                         if "404" in str(tmp_manager.last_error):
                             st.warning("💡 Dica: Erro 404 geralmente significa que a planilha não existe ou não foi compartilhada com o email da conta de serviço.")
                             st.info(f"Email da conta de serviço: {tmp_creds.get('client_email', 'Não encontrado')}")
                         if "403" in str(tmp_manager.last_error):
                             st.warning("💡 Dica: Erro 403 significa permissão negada. Verifique se a API do Google Sheets está ativada no console do Google Cloud.")
             except Exception as e:
                 st.error(f"Erro ao tentar diagnosticar conexão: {e}")

elif storage_backend == 'postgres' and not st.session_state.get('google_sheets_manager'):
    st.warning("⚠️ Postgres selecionado como backend, mas não foi possível conectar ao DATABASE_URL configurado.")
    st.write("Verifique as configurações de `st.secrets[\"DATABASE_URL\"]` ou a variável de ambiente `DATABASE_URL`.")
elif storage_backend == 'local':
    st.info("🔒 Usando armazenamento local. Nenhuma sincronização remota configurada.")
else:
    st.success("✅ Backend remoto conectado e pronto para sincronizar!")

st.markdown("---")

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "📋 Kanban", "✏️ Gerenciar", "⚙️ Configurações"])

# ============= TAB 1: DASHBOARD =============
with tab1:
    st.header("Dashboard Principal")
    
    # Debug: Mostrar contagem de dados
    col_debug1, col_debug2, col_debug3 = st.columns(3)
    with col_debug1:
        st.metric("Projetos", len(st.session_state.projetos))
    with col_debug2:
        st.metric("Etapas", len(st.session_state.etapas))
    with col_debug3:
        st.metric("Demandas", len(st.session_state.demandas))
    
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
        st.subheader("Sincronização Remota")
        backend = st.session_state.get('storage_backend', 'local')
        if backend == 'local':
            st.info("Nenhum backend remoto configurado. Selecione Postgres ou Google Sheets nas configurações.")
        else:
            if st.button("🔄 Carregar dados remotos"):
                carregar_dados()
            if st.button("💾 Salvar dados remotos"):
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

    # Storage Backend Selector
    st.subheader("🔁 Backend de Armazenamento")
    # Detect available options
    available_backends = ["local"]
    try:
        db_url = st.secrets.get("DATABASE_URL") if "DATABASE_URL" in st.secrets else os.environ.get('DATABASE_URL')
    except Exception:
        db_url = os.environ.get('DATABASE_URL')
    if db_url:
        available_backends.insert(0, "postgres")

    # detect google availability
    google_possible = False
    if "GOOGLE_CREDENTIALS" in st.secrets or ("type" in st.secrets and st.secrets.get("type") == "service_account") or os.path.exists("credentials.json"):
        google_possible = True
    if google_possible:
        available_backends.insert(0, "google")

    # default selection
    if "storage_backend" not in st.session_state:
        st.session_state.storage_backend = st.session_state.get('storage_backend', 'local')

    sel = st.selectbox("Escolha o backend de armazenamento:", options=available_backends, index=available_backends.index(st.session_state.storage_backend) if st.session_state.storage_backend in available_backends else 0)
    if sel != st.session_state.storage_backend:
        st.session_state.storage_backend = sel
        # Try to initialize the selected backend if required
        if sel == 'postgres':
            try:
                db_url = st.secrets.get("DATABASE_URL") if "DATABASE_URL" in st.secrets else os.environ.get('DATABASE_URL')
                pgm = PostgresManager(db_url)
                if pgm.connected:
                    st.session_state.google_sheets_manager = pgm
                    st.success("✅ Postgres configurado e conectado")
                else:
                    st.session_state.google_sheets_manager = None
                    st.error("❌ Não foi possível conectar ao Postgres")
            except Exception as e:
                st.session_state.google_sheets_manager = None
                st.error(f"❌ Erro ao conectar Postgres: {e}")
        elif sel == 'google':
            # Try to initialize the Google manager from secrets or local file
            try:
                if "GOOGLE_CREDENTIALS" in st.secrets:
                    secrets_creds = st.secrets["GOOGLE_CREDENTIALS"]
                    manager = GoogleSheetsManager(secrets_creds)
                    if manager.connected:
                        st.session_state.google_sheets_manager = manager
                        st.success("✅ Google Sheets configurado e conectado")
                    else:
                        st.session_state.google_sheets_manager = None
                        st.error("❌ Não foi possível conectar ao Google Sheets")
                elif os.path.exists("credentials.json"):
                    manager = GoogleSheetsManager("credentials.json")
                    if manager.connected:
                        st.session_state.google_sheets_manager = manager
                        st.success("✅ Google Sheets configurado e conectado via arquivo local")
                    else:
                        st.session_state.google_sheets_manager = None
                        st.error("❌ Não foi possível conectar ao Google Sheets via arquivo local")
                else:
                    st.error("Nenhuma credencial do Google encontrada. Configure st.secrets ou coloque credentials.json")
            except Exception as e:
                st.session_state.google_sheets_manager = None
                st.error(f"❌ Erro ao conectar Google Sheets: {e}")
        else:
            st.session_state.google_sheets_manager = None
            st.success("🔒 Usando armazenamento local")
    # Extra: botão de testar conexão para Postgres
    if st.session_state.storage_backend == 'postgres':
        db_url = None
        try:
            db_url = st.secrets.get("DATABASE_URL") if "DATABASE_URL" in st.secrets else os.environ.get('DATABASE_URL')
        except Exception:
            db_url = os.environ.get('DATABASE_URL')

        def _mask_db_url(url: str) -> str:
            if not url:
                return 'Nenhum DATABASE_URL configurado'
            try:
                # simples mascaramento: substitui senha entre : and @ por ***
                import re
                return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', url)
            except Exception:
                return '***'

        st.write("**DATABASE_URL:**", _mask_db_url(db_url))
        if st.button("🔍 Testar conexão Postgres"):
            try:
                if not db_url:
                    st.error('DATABASE_URL não encontrado em st.secrets nem em variáveis de ambiente')
                else:
                    pgm = PostgresManager(db_url)
                    if pgm.connected:
                        # Show driver used
                        driver = getattr(pgm.engine, 'dialect', None)
                        driver_name = getattr(driver, 'name', None) if driver else None
                        ok = pgm.health_check() if hasattr(pgm, 'health_check') else False
                        if ok:
                            try:
                                n = len(pgm.load_projetos())
                                st.success(f'Conexão bem-sucedida! Driver: {driver_name} — Projetos carregados: {n}')
                            except Exception as e:
                                st.warning('Conectado, mas falha ao carregar dados: ' + str(e))
                        else:
                            st.error('Conectado ao driver, mas health_check falhou. Erro: ' + str(pgm.last_error))
                    else:
                        st.error('Falha ao conectar ao Postgres: ' + str(pgm.last_error))
            # Admin - limpar dados remotos
            st.markdown("---")
            st.subheader("⚠️ Admin: Limpar dados remotos")
            st.write("ATENÇÃO: Esta ação irá remover todos os registros do backend remoto selecionado.")
            st.write("Digite CONFIRMAR para ativar o botão de exclusão.")
            confirm_token = st.text_input("Digite CONFIRMAR para confirmar exclusão do banco:", value="", max_chars=20)
            if confirm_token == "CONFIRMAR":
                if st.button("🧹 Limpar dados remotos (CONFIRMAR)"):
                    try:
                        if st.session_state.storage_backend == 'postgres' and st.session_state.get('google_sheets_manager'):
                            pm = st.session_state.get('google_sheets_manager')
                            ok = pm.clear_all()
                            if ok:
                                st.success('Dados do Postgres limpos com sucesso')
                                st.session_state.projetos = []
                                st.session_state.demandas = []
                                st.session_state.etapas = []
                            else:
                                st.error('Falha ao limpar dados do Postgres')
                        elif st.session_state.storage_backend == 'google' and st.session_state.get('google_sheets_manager'):
                            gsm = st.session_state.get('google_sheets_manager')
                            st.session_state.projetos = []
                            st.session_state.demandas = []
                            st.session_state.etapas = []
                            try:
                                gsm.save_projetos([])
                                gsm.save_demandas([])
                                gsm.save_etapas([])
                                st.success('Dados do Google Sheets limpos com sucesso')
                            except Exception as e:
                                st.error('Falha ao salvar/limpar Google Sheets: ' + str(e))
                        else:
                            # Local cleanup
                            st.session_state.projetos = []
                            st.session_state.demandas = []
                            st.session_state.etapas = []
                            st.success('Dados locais limpos com sucesso')
                    except Exception as e:
                        st.error('Erro ao limpar dados remotos: ' + str(e))
                        import traceback
                        st.code(traceback.format_exc())
            except Exception as e:
                import traceback
                st.error('Erro ao testar conexão: ' + str(e))
                st.code(traceback.format_exc())
    
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
