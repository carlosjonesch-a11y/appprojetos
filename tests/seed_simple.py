import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.modules.postgres_manager import PostgresManager
from src.modules.models import Projeto, Demanda, Etapa

DB_URL = 'postgresql+pg8000://postgres:!Enrico18@localhost:5432/jones'
pm = PostgresManager(DB_URL)
if not pm.connected:
    print('DB not connected:', pm.last_error)
    sys.exit(1)

# Clear DB first (start clean)
pm.clear_all()

# Create projetos
projetos = [
    Projeto(id='proj_1', nome='Portal Interno', descricao='Portal para acessos internos', status='Ativo', responsavel='Enrico'),
    Projeto(id='proj_2', nome='Aplicativo Mobile', descricao='App mobile para pedidos', status='Ativo', responsavel='Carlos'),
    Projeto(id='proj_3', nome='Relatórios BI', descricao='BI dashboard e relatórios', status='Ativo', responsavel='Ana'),
]

# Create demandas
demandas = [
    Demanda(id='dem_1', titulo='Login SSO', descricao='Implementar login único', projeto_id='proj_1', status='Pendente', prioridade='Alta', responsavel='Enrico'),
    Demanda(id='dem_2', titulo='Cadastro de usuário', descricao='Form de cadastro com validação', projeto_id='proj_1', status='Em Progresso', prioridade='Média', responsavel='Ana'),
    Demanda(id='dem_3', titulo='Push Notifications', descricao='Enviar notificações push no app', projeto_id='proj_2', status='Pendente', prioridade='Alta', responsavel='Carlos'),
    Demanda(id='dem_4', titulo='Relatório financeiro', descricao='Visualizações do financeiro', projeto_id='proj_3', status='Pendente', prioridade='Média', responsavel='Paula'),
]

# Create etapas
etapas = [
    Etapa(id='eta_1', nome='Especificação', descricao='Documento de requisitos', ordem=1),
    Etapa(id='eta_2', nome='Desenvolvimento', descricao='Desenvolvimento backend e frontend', ordem=2),
    Etapa(id='eta_3', nome='Teste', descricao='QA e testes automatizados', ordem=3),
    Etapa(id='eta_4', nome='Implementação inicial', descricao='Configuração do ambiente', ordem=1),
    Etapa(id='eta_5', nome='Entrega', descricao='Deploy e validação', ordem=2),
    Etapa(id='eta_6', nome='Design Mobile', descricao='Design tela de notificações', ordem=1),
]

print('Saving projetos...')
pm.save_projetos(projetos)
print('Saving demandas...')
pm.save_demandas(demandas)
print('Saving etapas...')
pm.save_etapas(etapas)

print('Seed simple complete')
print('Counts -> projetos:', len(pm.load_projetos()), 'demandas:', len(pm.load_demandas()), 'etapas:', len(pm.load_etapas()))
