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

class GoogleSheetsManager:
    """Gerenciador de integração com Google Sheets"""
    
    def __init__(self, credentials_json=None):
        """
        Inicializa o gerenciador do Google Sheets
        
        Args:
            credentials_json: Caminho do arquivo de credenciais JSON ou dict com as credenciais
        """
        self.last_error = None
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]

            if isinstance(credentials_json, dict):
                # Se for um dicionário (vindo de Streamlit secrets)
                # Corrige formatação da chave privada se necessário
                if "private_key" in credentials_json:
                    credentials_json["private_key"] = credentials_json["private_key"].replace("\\n", "\n")
                
                creds = Credentials.from_service_account_info(credentials_json, scopes=scopes)
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
            if "SPREADSHEET_ID" in st.secrets:
                sheet_id = st.secrets["SPREADSHEET_ID"]
            
            self.spreadsheet = self.gc.open_by_key(sheet_id)
            self.connected = True
        except Exception as e:
            self.last_error = str(e)
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
