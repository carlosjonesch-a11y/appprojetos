import traceback
import os
import sys
# Add project root to sys.path so `src` package can be imported when running this script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.modules.google_sheets_manager import GoogleSheetsManager
import json

print('Iniciando teste local do GoogleSheetsManager')

try:
    gsm = GoogleSheetsManager('credentials.json')
    print('Connected:', gsm.connected)
    print('Last error:', gsm.last_error)
    if gsm.connected:
        try:
            projetos = gsm.load_projetos()
            demandas = gsm.load_demandas()
            etapas = gsm.load_etapas()
            print(f'Projetos: {len(projetos)}; Demandas: {len(demandas)}; Etapas: {len(etapas)}')
        except Exception as e:
            print('Erro ao carregar dados:', e)
            traceback.print_exc()
except Exception as e:
    print('Erro criando GoogleSheetsManager:', e)
    traceback.print_exc()

print('\n--- Testando passando credentials como dict (simula st.secrets) ---')
try:
    with open('credentials.json', 'r', encoding='utf-8') as f:
        cred_dict = json.load(f)
    gsm2 = GoogleSheetsManager(cred_dict)
    print('Connected (dict):', gsm2.connected)
    print('Last error (dict):', gsm2.last_error)
    if gsm2.connected:
        projetos = gsm2.load_projetos()
        demandas = gsm2.load_demandas()
        etapas = gsm2.load_etapas()
        print(f'Projetos(dict): {len(projetos)}; Demandas(dict): {len(demandas)}; Etapas(dict): {len(etapas)}')
except Exception as e:
    print('Erro criando GoogleSheetsManager com dict:', e)
    traceback.print_exc()

print('\n--- Testando parsing direto com cryptography ---')
try:
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.primitives import serialization
    with open('credentials.json', 'r', encoding='utf-8') as f:
        cred = json.load(f)
    pk = cred.get('private_key')
    if isinstance(pk, (bytes, bytearray)):
        pk_bytes = pk
    else:
        # Normalize line endings
        pk_str = str(pk).replace('\\r\\n', '\\n').replace('\\r', '\\n')
        pk_bytes = pk_str.encode('utf-8')
    try:
        loaded = load_pem_private_key(pk_bytes, password=None)
        print('Cryptography: chave PEM carregada com sucesso (tipo):', type(loaded))
    except Exception as e_pk:
        print('Cryptography: falha ao carregar private key:', e_pk)
        import traceback as tb
        tb.print_exc()
except Exception as e:
    print('Erro testando parsing com cryptography:', e)
    traceback.print_exc()

print('\n--- Testando PostgresManager (SQLite em memória como substituto) ---')
try:
    from src.modules.postgres_manager import PostgresManager
    pm = PostgresManager('sqlite:///:memory:')
    print('PostgresManager conectado (sqlite in-memory):', pm.connected)
    # Cria e salva um projeto de teste
    from src.modules.models import Projeto
    p = Projeto(id='test1', nome='Teste', descricao='Projeto de teste')
    ok = pm.save_projetos([p])
    print('Save projetos returned:', ok)
    projetos = pm.load_projetos()
    print('Projetos carregados via PostgresManager:', len(projetos))
    # Health check
    try:
        ok_health = pm.health_check()
        print('Health check:', ok_health)
    except Exception as e:
        print('Health check failed:', e)

    # Test delete_projeto
    try:
        deleted = pm.delete_projeto('test1')
        print('delete_projeto returned:', deleted)
        projetos_after = pm.load_projetos()
        print('Projetos after delete:', len(projetos_after))
    except Exception as e:
        print('delete_projeto error:', e)

    # Clear all: save multiple and then clear
    try:
        p2 = Projeto(id='test2', nome='Teste2', descricao='Outro teste')
        p3 = Projeto(id='test3', nome='Teste3', descricao='Mais um teste')
        ok = pm.save_projetos([p2, p3])
        print('Save p2,p3 returned:', ok)
        projetos_before_clear = pm.load_projetos()
        print('Projetos before clear:', len(projetos_before_clear))
        cleared = pm.clear_all()
        print('clear_all returned:', cleared)
        projetos_after_clear = pm.load_projetos()
        print('Projetos after clear:', len(projetos_after_clear))
    except Exception as e:
        print('clear_all error:', e)
except ModuleNotFoundError as mnf:
    print('PostgresManager dependências faltando (instale sqlalchemy):', mnf)
except Exception as e:
    print('Erro testando PostgresManager:', e)
    traceback.print_exc()
