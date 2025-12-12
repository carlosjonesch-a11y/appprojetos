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

print('Clearing DB...')
pm.clear_all()

# Create 10 projects
projetos = []
for i in range(1, 11):
    p = Projeto(
        id=f'proj_{i}',
        nome=f'Projeto {i}',
        descricao=f'Descrição do projeto {i}',
        status='Ativo',
        responsavel=f'Responsavel {((i-1)%5)+1}'
    )
    projetos.append(p)

# Create 5 etapas
etapas = []
for i in range(1, 6):
    e = Etapa(
        id=f'eta_{i}',
        nome=f'Etapa {i}',
        descricao=f'Descrição da etapa {i}',
        ordem=i
    )
    etapas.append(e)

# Create 100 demandas distributed across projects
prioridades = ['Baixa', 'Média', 'Alta', 'Crítica']
statuses = ['Pendente', 'Em Progresso', 'Concluído']
responsaveis = ['Enrico', 'Carlos', 'Ana', 'Paula', 'Mariana']

demandas = []
for i in range(1, 101):
    projeto_idx = ((i-1) % 10) + 1
    etapa_idx = ((i-1) % 5) + 1
    dem = Demanda(
        id=f'dem_{i}',
        titulo=f'Demanda {i}',
        descricao=f'Descrição da demanda {i}',
        projeto_id=f'proj_{projeto_idx}',
        status=statuses[i % len(statuses)],
        prioridade=prioridades[i % len(prioridades)],
        responsavel=responsaveis[i % len(responsaveis)],
        data_vencimento=None
    )
    # assign etapa_id to half of demandas
    if i % 2 == 0:
        dem.etapa_id = f'eta_{etapa_idx}'
    demandas.append(dem)

print('Saving projetos...')
pm.save_projetos(projetos)
print('Saving demandas...')
pm.save_demandas(demandas)
print('Saving etapas...')
pm.save_etapas(etapas)

print('Bulk seed complete')
print('Counts -> projetos:', len(pm.load_projetos()), 'demandas:', len(pm.load_demandas()), 'etapas:', len(pm.load_etapas()))
