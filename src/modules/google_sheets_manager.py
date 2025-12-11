import gspread
import json
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any
import streamlit as st
from google.oauth2.service_account import Credentials
from src.modules.models import Projeto, Demanda, Etapa, StatusEnum, PriorityEnum

# ID da planilha Google Sheets
SPREADSHEET_ID = "1cyZg-dt1BR4K7pTKvx5o8rWKP7_uNHrDQDdlYedTQI0"

import traceback

class GoogleSheetsManager:
    """Gerenciador de integração com Google Sheets"""
    
    def __init__(self, credentials_json=None):
        """
        Inicializa o gerenciador do Google Sheets
        
        Args:
            credentials_json: Caminho do arquivo de credenciais JSON ou dict com as credenciais
        """
        self.last_error = None
        self.error_traceback = None
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]

            # Converte para dict se for um objeto parecido com dict (como AttrDict do Streamlit)
            if hasattr(credentials_json, "to_dict"):
                credentials_json = credentials_json.to_dict()
            elif hasattr(credentials_json, "keys") and not isinstance(credentials_json, dict):
                credentials_json = dict(credentials_json)

            if isinstance(credentials_json, dict):
                # Se for um dicionário (vindo de Streamlit secrets)
                creds_dict = dict(credentials_json)

                # We will use the file-based approach as primary for dict-like credentials
                # to avoid pyasn1/RA issues on Streamlit Cloud. This also normalizes the key.
                try:
                    # Normalize and sanitize private_key to safe PEM format
                    if 'private_key' in creds_dict:
                        pk_val = creds_dict['private_key']
                        if isinstance(pk_val, (bytes, bytearray)):
                            pk_str = pk_val.decode('utf-8')
                        else:
                            pk_str = str(pk_val)
                        # Convert literal '\\n' sequences and windows CRLFs
                        pk_str = pk_str.replace('\\r\\n', '\n').replace('\\r', '\n')
                        pk_str = pk_str.replace('\\n', '\n')
                        # strip spaces from lines and ensure begin/end lines exist
                        lines = [l.strip() for l in pk_str.splitlines() if l.strip()]
                        if lines and not lines[0].startswith('-----BEGIN'):
                            # attempt to find the header
                            joined = '\n'.join(lines)
                            pos = joined.find('-----BEGIN')
                            if pos != -1:
                                joined = joined[pos:]
                            pk_str = joined
                        else:
                            pk_str = '\n'.join(lines)
                        creds_dict['private_key'] = pk_str

                    # Write creds to a temp file and use from_service_account_file — this avoids
                    # the pyasn1 string vs file issues of google-auth in some linux/Python builds.
                    import tempfile, os
                    tmpfile = None
                    try:
                        tmpf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
                        json.dump(creds_dict, tmpf, ensure_ascii=False)
                        tmpf.flush()
                        tmpf.close()
                        tmpfile = tmpf.name
                        # Masked log: show beginning and length only
                        masked = str(creds_dict.get('private_key', '')[:25]) + '...'
                        print(f"DEBUG: Temp credentials written to: {tmpfile} (private_key start: {masked} len={len(creds_dict.get('private_key',''))})")
                        creds = Credentials.from_service_account_file(tmpfile, scopes=scopes)
                        # Remove temp file right after parse
                        try:
                            os.unlink(tmpfile)
                        except Exception:
                            pass
                    finally:
                        # If tmpfile still exists remove it
                        try:
                            if tmpfile and os.path.exists(tmpfile):
                                os.unlink(tmpfile)
                        except Exception:
                            pass

                    self.gc = gspread.authorize(creds)
                    
                    from google.auth import crypt
                    from google.oauth2 import service_account
                    # Debug: tipos/infos da chave
                    try:
                        pk_debug = creds_dict.get("private_key")
                        print("DEBUG: private_key tipo (antes):", type(pk_debug))
                        if isinstance(pk_debug, str):
                            print("DEBUG: private_key sample (masked):", "<masked-start>" + pk_debug[:20] + "...")
                            print("DEBUG: private_key length:", len(pk_debug))
                    except Exception:
                        pass
                    
                    if "private_key" in creds_dict and "client_email" in creds_dict:
                        pk = creds_dict["private_key"]
                        # Normalize string: ensure windows newlines and \n escaped sequences are proper
                        if isinstance(pk, (bytes, bytearray)):
                            try:
                                pk_str = pk.decode("utf-8")
                            except Exception:
                                pk_str = str(pk)
                        else:
                            pk_str = str(pk)

                        # Normalize escapes and line endings
                        pk_str = pk_str.replace('\\r\\n', '\n')
                        pk_str = pk_str.replace('\\n', '\n')
                        pk_str = pk_str.replace('\r\n', '\n')
                        pk_str = pk_str.replace('\r', '\n')
                        # Trim spaces on each line
                        pk_lines = [line.strip() for line in pk_str.splitlines() if line.strip()]
                        # Reconstruct sanitized pk string
                        pk_sanitized = '\n'.join(pk_lines)
                        # Ensure header/footer are correct
                        if not pk_sanitized.startswith('-----BEGIN '):
                            # Try to detect header
                            pos = pk_sanitized.find('-----BEGIN')
                            if pos != -1:
                                pk_sanitized = pk_sanitized[pos:]
                        
                        # Convert to bytes for parsing
                        pk_bytes = pk_sanitized.encode('utf-8')
                        # Debug: confirmar tipo
                        print("DEBUG: pk_bytes type:", type(pk_bytes), "len:", len(pk_bytes) if hasattr(pk_bytes, '__len__') else 'n/a')
                        # Try original crypt.RSASigner.from_string first
                        try:
                            signer = crypt.RSASigner.from_string(pk_bytes)
                        except Exception as exc_signer:
                            print("DEBUG: RSASigner.from_string failed:", exc_signer)
                            # Try to load with cryptography and create a simple signer wrapper
                            try:
                                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                                from cryptography.hazmat.primitives.asymmetric import padding
                                from cryptography.hazmat.primitives import hashes
                                private_key_obj = load_pem_private_key(pk_bytes, password=None)
                                class SignerWrapper:
                                    def __init__(self, keyobj):
                                        self._keyobj = keyobj
                                    def sign(self, message):
                                        return self._keyobj.sign(message, padding.PKCS1v15(), hashes.SHA256())
                                signer = SignerWrapper(private_key_obj)
                                print("DEBUG: SignerWrapper criado com sucesso usando cryptography")
                            except Exception as exc_crypt:
                                print("DEBUG: Fallback cryptography parsing falhou:", exc_crypt)
                                # Ultimo recurso: escrever em arquivo temporario e usar from_service_account_file
                                try:
                                    import tempfile
                                    import os
                                    tmp = None
                                    creds_copy = dict(creds_dict)
                                    # Ensure private key is string with proper newlines
                                    if isinstance(creds_copy.get('private_key'), (bytes, bytearray)):
                                        creds_copy['private_key'] = creds_copy['private_key'].decode('utf-8')
                                    tmpf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                                    json.dump(creds_copy, tmpf)
                                    tmpf.flush()
                                    tmpf.close()
                                    print(f"DEBUG: Escritor temporario criado em: {tmpf.name}")
                                    creds = Credentials.from_service_account_file(tmpf.name, scopes=scopes)
                                    os.unlink(tmpf.name)
                                    self.gc = gspread.authorize(creds)
                                    # Se chegou aqui, retornamos
                                    self.connected = True
                                    return
                                except Exception as exc_file:
                                    print('DEBUG: Fallback de arquivo falhou:', exc_file)
                                    raise
                        creds = service_account.Credentials(
                            signer,
                            service_account_email=creds_dict["client_email"],
                            token_uri=creds_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
                            scopes=scopes,
                            project_id=creds_dict.get("project_id")
                        )
                    else:
                        raise e_std

                self.gc = gspread.authorize(creds)
                
            elif isinstance(credentials_json, str):
                # Verifica se é uma string JSON ou um caminho de arquivo
                if credentials_json.strip().startswith("{"):
                    # É uma string JSON
                    info = json.loads(credentials_json)
                    if "private_key" in info:
                        info["private_key"] = info["private_key"].replace("\\n", "\n")
                    creds = Credentials.from_service_account_info(info, scopes=scopes)
                else:
                    # É um caminho de arquivo
                    creds = Credentials.from_service_account_file(credentials_json, scopes=scopes)
                
                self.gc = gspread.authorize(creds)
            else:
                raise ValueError(f"Tipo de credencial inválido: {type(credentials_json)}")
            
            # Tenta pegar ID da planilha das secrets se disponível, senão usa o hardcoded
            sheet_id = SPREADSHEET_ID
            try:
                if "SPREADSHEET_ID" in st.secrets:
                    sheet_id = st.secrets["SPREADSHEET_ID"]
            except FileNotFoundError:
                # No local Streamlit secrets file; keep default
                pass
            
            self.spreadsheet = self.gc.open_by_key(sheet_id)
            self.connected = True
        except Exception as e:
            self.last_error = str(e)
            self.error_traceback = traceback.format_exc()
            print(f"DEBUG: Erro no GoogleSheetsManager: {e}")
            print(self.error_traceback)
            st.error(f"Erro ao conectar ao Google Sheets: {e}")
            self.connected = False
    
    def get_or_create_worksheet(self, worksheet_name: str):
        """Obtém ou cria uma aba na planilha"""
        try:
            return self.spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
    
    def save_projetos(self, projetos: List[Projeto]):
        """Salva lista de projetos no Google Sheets"""
        if not self.connected:
            st.error("Não conectado ao Google Sheets")
            return False
        
        try:
            worksheet = self.get_or_create_worksheet("Projetos")
            
            # Limpa a planilha
            worksheet.clear()
            
            # Headers
            headers = ["id", "nome", "descricao", "status", "responsavel", "data_criacao", "data_conclusao"]
            worksheet.append_row(headers)
            
            # Dados
            for projeto in projetos:
                row = [
                    projeto.id,
                    projeto.nome,
                    projeto.descricao,
                    projeto.status,
                    projeto.responsavel or "",
                    projeto.data_criacao,
                    projeto.data_conclusao or ""
                ]
                worksheet.append_row(row)
            
            return True
        except Exception as e:
            st.error(f"Erro ao salvar projetos: {e}")
            return False
    
    def save_demandas(self, demandas: List[Demanda]):
        """Salva lista de demandas no Google Sheets"""
        if not self.connected:
            st.error("Não conectado ao Google Sheets")
            return False
        
        try:
            worksheet = self.get_or_create_worksheet("Demandas")
            
            # Limpa a planilha
            worksheet.clear()
            
            # Headers com os novos campos de data
            headers = ["id", "titulo", "descricao", "projeto_id", "status", "prioridade", 
                      "responsavel", "etapa_id", "data_inicio_plano", "data_inicio_real",
                      "data_vencimento_plano", "data_vencimento_real", "data_vencimento", 
                      "data_criacao", "data_conclusao", "percentual_completo", "tags", "comentarios"]
            worksheet.append_row(headers)
            
            # Dados
            for demanda in demandas:
                row = [
                    demanda.id,
                    demanda.titulo,
                    demanda.descricao,
                    demanda.projeto_id,
                    demanda.status,
                    demanda.prioridade,
                    demanda.responsavel or "",
                    demanda.etapa_id or "",
                    demanda.data_inicio_plano or "",
                    demanda.data_inicio_real or "",
                    demanda.data_vencimento_plano or "",
                    demanda.data_vencimento_real or "",
                    demanda.data_vencimento or "",
                    demanda.data_criacao,
                    demanda.data_conclusao or "",
                    demanda.percentual_completo,
                    "|".join(demanda.tags) if demanda.tags else "",
                    "|".join(demanda.comentarios) if demanda.comentarios else ""
                ]
                worksheet.append_row(row)
            
            return True
        except Exception as e:
            st.error(f"Erro ao salvar demandas: {e}")
            return False
    
    def save_etapas(self, etapas: List[Etapa]):
        """Salva lista de etapas no Google Sheets"""
        if not self.connected:
            st.error("Não conectado ao Google Sheets")
            return False
        
        try:
            worksheet = self.get_or_create_worksheet("Etapas")
            
            # Limpa a planilha
            worksheet.clear()
            
            # Headers
            headers = ["id", "nome", "descricao", "ordem", "data_criacao"]
            worksheet.append_row(headers)
            
            # Dados
            for etapa in etapas:
                row = [
                    etapa.id,
                    etapa.nome,
                    etapa.descricao,
                    str(etapa.ordem),
                    etapa.data_criacao
                ]
                worksheet.append_row(row)
            
            return True
        except Exception as e:
            st.error(f"Erro ao salvar etapas: {e}")
            return False
    
    def load_projetos(self) -> List[Projeto]:
        """Carrega lista de projetos do Google Sheets"""
        if not self.connected:
            return []
        
        try:
            worksheet = self.get_or_create_worksheet("Projetos")
            
            data = worksheet.get_all_records()
            projetos = []
            
            for row in data:
                projeto = Projeto(
                    id=row.get("id", ""),
                    nome=row.get("nome", ""),
                    descricao=row.get("descricao", ""),
                    status=row.get("status", StatusEnum.TODO.value),
                    responsavel=row.get("responsavel") or None,
                    data_criacao=row.get("data_criacao", datetime.now().isoformat()),
                    data_conclusao=row.get("data_conclusao") or None
                )
                projetos.append(projeto)
            
            return projetos
        except gspread.exceptions.APIError as e:
            if "403" in str(e):
                pass  # Silenciar erros de cota - app continua funcionando
            else:
                st.error(f"Erro ao carregar projetos: {e}")
            return []
        except Exception as e:
            pass  # Silenciar outros erros também
            return []
    
    def load_demandas(self) -> List[Demanda]:
        """Carrega lista de demandas do Google Sheets"""
        if not self.connected:
            return []
        
        try:
            worksheet = self.get_or_create_worksheet("Demandas")
            
            data = worksheet.get_all_records()
            demandas = []
            
            for row in data:
                tags = row.get("tags", "").split("|") if row.get("tags") else []
                comentarios = row.get("comentarios", "").split("|") if row.get("comentarios") else []
                
                demanda = Demanda(
                    id=row.get("id", ""),
                    titulo=row.get("titulo", ""),
                    descricao=row.get("descricao", ""),
                    projeto_id=row.get("projeto_id", ""),
                    status=row.get("status", StatusEnum.TODO.value),
                    prioridade=row.get("prioridade", PriorityEnum.MEDIA.value),
                    responsavel=row.get("responsavel") or None,
                    etapa_id=row.get("etapa_id") or None,
                    data_vencimento=row.get("data_vencimento") or None,
                    data_inicio_plano=row.get("data_inicio_plano") or None,
                    data_inicio_real=row.get("data_inicio_real") or None,
                    data_vencimento_plano=row.get("data_vencimento_plano") or None,
                    data_vencimento_real=row.get("data_vencimento_real") or None,
                    data_criacao=row.get("data_criacao", datetime.now().isoformat()),
                    data_conclusao=row.get("data_conclusao") or None,
                    percentual_completo=int(row.get("percentual_completo", 0)) if row.get("percentual_completo") else 0,
                    tags=[t for t in tags if t],
                    comentarios=[c for c in comentarios if c]
                )
                demandas.append(demanda)
            
            return demandas
        except gspread.exceptions.APIError as e:
            if "403" in str(e):
                pass  # Silenciar erros de cota - app continua funcionando
            else:
                st.error(f"Erro ao carregar demandas: {e}")
            return []
        except Exception as e:
            pass  # Silenciar outros erros também
            return []
    
    def load_etapas(self) -> List[Etapa]:
        """Carrega lista de etapas do Google Sheets"""
        if not self.connected:
            return []
        
        try:
            worksheet = self.get_or_create_worksheet("Etapas")
            
            data = worksheet.get_all_records()
            etapas = []
            
            for row in data:
                etapa = Etapa(
                    id=row.get("id", ""),
                    nome=row.get("nome", ""),
                    descricao=row.get("descricao", ""),
                    ordem=int(row.get("ordem", 0)),
                    data_criacao=row.get("data_criacao", datetime.now().isoformat())
                )
                etapas.append(etapa)
            
            return etapas
        except gspread.exceptions.APIError as e:
            if "403" in str(e):
                pass  # Silenciar erros de cota - app continua funcionando
            else:
                st.error(f"Erro ao carregar etapas: {e}")
            return []
        except Exception as e:
            pass  # Silenciar outros erros também
            return []
