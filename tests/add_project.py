import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.modules.postgres_manager import PostgresManager
from src.modules.models import Projeto

pm = PostgresManager('postgresql+pg8000://postgres:!Enrico18@localhost:5432/jones')
if not pm.connected:
    print('DB not connected:', pm.last_error)
else:
    projetos = pm.load_projetos()
    pid = f"proj_{len(projetos)+1}"
    p = Projeto(id=pid, nome="Teste via script", descricao="Criado durante testes", status="Ativo", responsavel="Tester")
    projetos.append(p)
    pm.save_projetos(projetos)
    print('Projeto salvo:', pid)
