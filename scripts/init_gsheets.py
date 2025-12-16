"""Script para inicializar a estrutura da planilha Google Sheets."""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.google_sheets_manager import GoogleSheetsManager


def init_gsheets():
    """Inicializa a estrutura da planilha Google Sheets."""
    
    # Carregar configuração do secrets
    try:
        import streamlit as st
        spreadsheet_id = st.secrets.get("GSHEETS_SPREADSHEET_ID")
        service_account_info = st.secrets.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    except Exception:
        # Fallback para variáveis de ambiente ou secrets.toml manual
        import toml
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")
        
        if not os.path.exists(secrets_path):
            print("❌ Arquivo .streamlit/secrets.toml não encontrado!")
            print("Configure GSHEETS_SPREADSHEET_ID e GOOGLE_SERVICE_ACCOUNT_JSON")
            return False
            
        secrets = toml.load(secrets_path)
        spreadsheet_id = secrets.get("GSHEETS_SPREADSHEET_ID")
        service_account_json = secrets.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        
        if isinstance(service_account_json, str):
            import json
            service_account_info = json.loads(service_account_json)
        else:
            service_account_info = service_account_json
    
    if not spreadsheet_id or not service_account_info:
        print("❌ Configurações não encontradas!")
        return False
    
    # Garantir que service_account_info é dict
    if isinstance(service_account_info, str):
        import json
        service_account_info = json.loads(service_account_info)
    
    print(f"📊 Inicializando planilha: {spreadsheet_id}")
    print(f"🔑 Service Account: {service_account_info.get('client_email', 'N/A')}")
    
    try:
        manager = GoogleSheetsManager(spreadsheet_id, service_account_info)
        
        print("\n🔄 Testando conexão e criando estrutura...")
        success = manager.health_check()
        
        if success:
            print("\n✅ Estrutura criada com sucesso!")
            print("\nAbas criadas:")
            print("  - projetos")
            print("  - demandas")
            print("  - etapas")
            print("  - checklist_topics")
            print("  - checklist_tasks")
            
            # Verificar se consegue ler
            print("\n🔍 Verificando leitura...")
            projetos = manager.load_projetos()
            demandas = manager.load_demandas()
            etapas = manager.load_etapas()
            
            print(f"  - Projetos: {len(projetos)}")
            print(f"  - Demandas: {len(demandas)}")
            print(f"  - Etapas: {len(etapas)}")
            
            print("\n🎉 Tudo pronto! Você pode iniciar o app agora.")
            return True
        else:
            print("❌ Erro ao criar estrutura")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_gsheets()
    sys.exit(0 if success else 1)
