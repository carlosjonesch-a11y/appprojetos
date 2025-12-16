import sys
from pathlib import Path
import os
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.modules.postgres_manager import PostgresManager

db_url = os.getenv('DATABASE_URL')
if not db_url:
	raise SystemExit(
		"DATABASE_URL não configurado. Defina a variável de ambiente DATABASE_URL antes de rodar este script."
	)
pm = PostgresManager(db_url)
print('Conectado:', pm.connected)
print('Database URL:', pm.database_url)
print('Last error:', pm.last_error)
print('Health check:', pm.health_check())
print('Projetos count:', len(pm.load_projetos()))
print('Demandas count:', len(pm.load_demandas()))
print('Etapas count:', len(pm.load_etapas()))
