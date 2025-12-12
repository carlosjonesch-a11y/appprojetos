import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.modules.postgres_manager import PostgresManager

pm = PostgresManager('postgresql+pg8000://postgres:!Enrico18@localhost:5432/jones')
print('Conectado:', pm.connected)
print('Database URL:', pm.database_url)
print('Last error:', pm.last_error)
print('Health check:', pm.health_check())
print('Projetos count:', len(pm.load_projetos()))
print('Demandas count:', len(pm.load_demandas()))
print('Etapas count:', len(pm.load_etapas()))
