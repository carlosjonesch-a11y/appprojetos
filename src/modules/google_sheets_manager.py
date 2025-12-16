import json
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from src.modules.models import Projeto, Demanda, Etapa


class GoogleSheetsManager:
    """Persistência em Google Planilhas (Google Sheets) via Service Account.

    Estrutura (abas/worksheets):
      - projetos
      - demandas
      - etapas
      - checklist_topics
      - checklist_tasks

    A API pública espelha o que o app usa (compatível com managers anteriores).
    """

    SHEET_PROJETOS = "projetos"
    SHEET_DEMANDAS = "demandas"
    SHEET_ETAPAS = "etapas"
    SHEET_CHECKLIST_TOPICS = "checklist_topics"
    SHEET_CHECKLIST_TASKS = "checklist_tasks"

    def __init__(self, spreadsheet_id: str, service_account_info: dict[str, Any]):
        self.database_url = "gsheets://" + str(spreadsheet_id)
        self.spreadsheet_id = str(spreadsheet_id)
        self._service_account_info = service_account_info
        self._client = None
        self._spreadsheet = None

    # ------------------------- Auth / client helpers -------------------------

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except Exception as e:
            raise RuntimeError(
                "Dependências Google Sheets não instaladas. Garanta gspread e google-auth no requirements.txt. Erro: "
                + str(e)
            )

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds = Credentials.from_service_account_info(self._service_account_info, scopes=scopes)
        self._client = gspread.authorize(creds)
        return self._client

    def _get_spreadsheet(self):
        if self._spreadsheet is not None:
            return self._spreadsheet
        client = self._get_client()
        try:
            self._spreadsheet = client.open_by_key(self.spreadsheet_id)
            return self._spreadsheet
        except Exception as e:
            raise RuntimeError(
                "Não foi possível abrir a planilha. Verifique se a planilha foi compartilhada com o e-mail do service account. Erro: "
                + str(e)
            )

    def _worksheet(self, title: str):
        ss = self._get_spreadsheet()
        try:
            return ss.worksheet(title)
        except Exception:
            return None

    def _ensure_worksheet(self, title: str, headers: list[str]):
        ss = self._get_spreadsheet()
        ws = self._worksheet(title)
        if ws is None:
            ws = ss.add_worksheet(title=title, rows=2000, cols=max(10, len(headers) + 2))
            if headers:
                ws.update([headers])
            return ws

        # Se existe, garantir cabeçalho minimamente correto
        try:
            first_row = ws.row_values(1)
        except Exception:
            first_row = []

        if not first_row and headers:
            ws.update([headers])
        elif headers:
            # Se já tem cabeçalho, não forçar overwrite para não apagar colunas extras do usuário.
            pass
        return ws

    # ------------------------- Dataframe helpers -------------------------

    @staticmethod
    def _to_cell_values(df: pd.DataFrame) -> list[list[Any]]:
        if df is None or df.empty:
            return []

        out = df.copy()
        out = out.where(pd.notnull(out), "")

        # Garantir listas como JSON (tags/comentarios)
        for col in ["tags", "comentarios"]:
            if col in out.columns:
                out[col] = out[col].apply(
                    lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else ("" if v == "" else str(v))
                )

        header = list(out.columns)
        rows: list[list[Any]] = [header]
        rows.extend(out.astype(str).values.tolist())
        return rows

    @staticmethod
    def _from_records(records: list[dict[str, Any]]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)

    def _read_df(self, title: str) -> pd.DataFrame:
        ws = self._worksheet(title)
        if ws is None:
            return pd.DataFrame()

        values = ws.get_all_values()
        if not values or len(values) < 2:
            return pd.DataFrame()

        header = values[0]
        rows = values[1:]
        df = pd.DataFrame(rows, columns=header)
        df = df.replace({"": None})

        # Normalizar tipos conhecidos
        if "ordem" in df.columns:
            df["ordem"] = pd.to_numeric(df["ordem"], errors="coerce").fillna(0).astype(int)
        if "percentual_completo" in df.columns:
            df["percentual_completo"] = pd.to_numeric(df["percentual_completo"], errors="coerce").fillna(0).astype(int)

        # Listas
        for col in ["tags", "comentarios"]:
            if col in df.columns:
                def _parse_list(v):
                    if v is None:
                        return []
                    s = str(v).strip()
                    if not s:
                        return []
                    try:
                        parsed = json.loads(s)
                        return parsed if isinstance(parsed, list) else []
                    except Exception:
                        return [s]

                df[col] = df[col].apply(_parse_list)

        return df

    def _write_df(self, title: str, df: pd.DataFrame, headers: list[str]):
        ws = self._ensure_worksheet(title, headers=headers)

        # Limpar e regravar (mais simples e consistente)
        ws.clear()
        if df is None or df.empty:
            ws.update([headers] if headers else [["id"]])
            return True

        values = self._to_cell_values(df)
        ws.update(values)
        return True

    # ------------------------- Public API (compat) -------------------------

    def health_check(self) -> bool:
        ss = self._get_spreadsheet()
        _ = ss.title
        # garantir worksheets core
        self._ensure_worksheet(self.SHEET_PROJETOS, headers=["id", "nome", "descricao", "status", "data_criacao", "data_conclusao", "responsavel"])
        self._ensure_worksheet(self.SHEET_ETAPAS, headers=["id", "nome", "descricao", "ordem", "data_criacao"])
        self._ensure_worksheet(
            self.SHEET_DEMANDAS,
            headers=[
                "id",
                "titulo",
                "descricao",
                "projeto_id",
                "status",
                "prioridade",
                "etapa_id",
                "responsavel",
                "data_inicio_plano",
                "data_inicio_real",
                "data_vencimento_plano",
                "data_vencimento_real",
                "data_vencimento",
                "data_criacao",
                "data_conclusao",
                "percentual_completo",
                "tags",
                "comentarios",
            ],
        )
        self._ensure_worksheet(self.SHEET_CHECKLIST_TOPICS, headers=["id", "nome", "created_at"])
        self._ensure_worksheet(self.SHEET_CHECKLIST_TASKS, headers=["id", "topic_id", "texto", "done", "created_at"])
        return True

    # ---- Projetos ----

    def load_projetos(self) -> list[Projeto]:
        df = self._read_df(self.SHEET_PROJETOS)
        if df.empty:
            return []
        out: list[Projeto] = []
        for _, row in df.iterrows():
            data = row.to_dict()
            data = {k: (None if v is None else v) for k, v in data.items()}
            out.append(Projeto.from_dict(data))
        return out

    def save_projetos(self, projetos: list[Projeto]) -> bool:
        rows = []
        for p in projetos:
            d = p.to_dict() if hasattr(p, "to_dict") else asdict(p)
            # Evitar embutir etapas/demandas no registro de projeto
            d.pop("etapas", None)
            d.pop("demandas", None)
            rows.append(d)
        df = pd.DataFrame(rows)
        headers = ["id", "nome", "descricao", "status", "data_criacao", "data_conclusao", "responsavel"]
        for h in headers:
            if h not in df.columns:
                df[h] = ""
        df = df[headers]
        return self._write_df(self.SHEET_PROJETOS, df, headers=headers)

    def delete_projeto(self, projeto_id: str) -> bool:
        projetos = [p for p in self.load_projetos() if getattr(p, "id", None) != projeto_id]
        return self.save_projetos(projetos)

    # ---- Etapas ----

    def load_etapas(self) -> list[Etapa]:
        df = self._read_df(self.SHEET_ETAPAS)
        if df.empty:
            return []
        out: list[Etapa] = []
        for _, row in df.iterrows():
            data = row.to_dict()
            out.append(Etapa.from_dict(data))
        return out

    def save_etapas(self, etapas: list[Etapa]) -> bool:
        rows = []
        for e in etapas:
            d = e.to_dict() if hasattr(e, "to_dict") else asdict(e)
            rows.append(d)
        df = pd.DataFrame(rows)
        headers = ["id", "nome", "descricao", "ordem", "data_criacao"]
        for h in headers:
            if h not in df.columns:
                df[h] = ""
        df = df[headers]
        return self._write_df(self.SHEET_ETAPAS, df, headers=headers)

    def delete_etapa(self, etapa_id: str) -> bool:
        etapas = [e for e in self.load_etapas() if getattr(e, "id", None) != etapa_id]
        return self.save_etapas(etapas)

    # ---- Demandas ----

    def load_demandas(self) -> list[Demanda]:
        df = self._read_df(self.SHEET_DEMANDAS)
        if df.empty:
            return []
        out: list[Demanda] = []
        for _, row in df.iterrows():
            data = row.to_dict()
            out.append(Demanda.from_dict(data))
        return out

    def save_demandas(self, demandas: list[Demanda]) -> bool:
        rows = []
        for d in demandas:
            row = d.to_dict() if hasattr(d, "to_dict") else asdict(d)
            rows.append(row)
        df = pd.DataFrame(rows)
        headers = [
            "id",
            "titulo",
            "descricao",
            "projeto_id",
            "status",
            "prioridade",
            "etapa_id",
            "responsavel",
            "data_inicio_plano",
            "data_inicio_real",
            "data_vencimento_plano",
            "data_vencimento_real",
            "data_vencimento",
            "data_criacao",
            "data_conclusao",
            "percentual_completo",
            "tags",
            "comentarios",
        ]
        for h in headers:
            if h not in df.columns:
                df[h] = ""
        df = df[headers]
        return self._write_df(self.SHEET_DEMANDAS, df, headers=headers)

    def delete_demanda(self, demanda_id: str) -> bool:
        demandas = [d for d in self.load_demandas() if getattr(d, "id", None) != demanda_id]
        return self.save_demandas(demandas)

    # ---- Limpeza ----

    def clear_core_data(self) -> bool:
        self._write_df(self.SHEET_PROJETOS, pd.DataFrame(), headers=["id", "nome", "descricao", "status", "data_criacao", "data_conclusao", "responsavel"])
        self._write_df(self.SHEET_ETAPAS, pd.DataFrame(), headers=["id", "nome", "descricao", "ordem", "data_criacao"])
        self._write_df(
            self.SHEET_DEMANDAS,
            pd.DataFrame(),
            headers=[
                "id",
                "titulo",
                "descricao",
                "projeto_id",
                "status",
                "prioridade",
                "etapa_id",
                "responsavel",
                "data_inicio_plano",
                "data_inicio_real",
                "data_vencimento_plano",
                "data_vencimento_real",
                "data_vencimento",
                "data_criacao",
                "data_conclusao",
                "percentual_completo",
                "tags",
                "comentarios",
            ],
        )
        return True

    def clear_all(self) -> bool:
        self.clear_core_data()
        self._write_df(self.SHEET_CHECKLIST_TOPICS, pd.DataFrame(), headers=["id", "nome", "created_at"])
        self._write_df(self.SHEET_CHECKLIST_TASKS, pd.DataFrame(), headers=["id", "topic_id", "texto", "done", "created_at"])
        return True

    # ---- Checklist ----

    def load_checklist_topics(self) -> list[dict[str, Any]]:
        df = self._read_df(self.SHEET_CHECKLIST_TOPICS)
        if df.empty:
            return []
        out = []
        for _, row in df.iterrows():
            out.append({"id": row.get("id"), "nome": row.get("nome"), "created_at": row.get("created_at")})
        return out

    def create_checklist_topic(self, nome: str) -> dict[str, Any]:
        topics = self.load_checklist_topics()
        topic_id = f"topic_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        item = {"id": topic_id, "nome": nome, "created_at": datetime.now().isoformat()}
        topics.append(item)
        df = pd.DataFrame(topics)
        self._write_df(self.SHEET_CHECKLIST_TOPICS, df, headers=["id", "nome", "created_at"])
        return item

    def rename_checklist_topic(self, topic_id: str, new_name: str) -> bool:
        topics = self.load_checklist_topics()
        for t in topics:
            if str(t.get("id")) == str(topic_id):
                t["nome"] = new_name
        df = pd.DataFrame(topics)
        self._write_df(self.SHEET_CHECKLIST_TOPICS, df, headers=["id", "nome", "created_at"])
        return True

    def load_checklist_tasks(self, topic_id: str) -> list[dict[str, Any]]:
        df = self._read_df(self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            return []
        df = df[df.get("topic_id") == topic_id]
        out = []
        for _, row in df.iterrows():
            done_raw = row.get("done")
            done = str(done_raw).lower() in ("1", "true", "yes", "sim")
            out.append(
                {
                    "id": row.get("id"),
                    "topic_id": row.get("topic_id"),
                    "texto": row.get("texto"),
                    "done": done,
                    "created_at": row.get("created_at"),
                }
            )
        return out

    def create_checklist_task(self, topic_id: str, texto: str) -> dict[str, Any]:
        df = self._read_df(self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            df = pd.DataFrame(columns=["id", "topic_id", "texto", "done", "created_at"])
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        item = {
            "id": task_id,
            "topic_id": topic_id,
            "texto": texto,
            "done": False,
            "created_at": datetime.now().isoformat(),
        }
        df = pd.concat([df, pd.DataFrame([item])], ignore_index=True)
        self._write_df(self.SHEET_CHECKLIST_TASKS, df, headers=["id", "topic_id", "texto", "done", "created_at"])
        return item

    def set_checklist_task_done(self, task_id: str, done: bool) -> bool:
        df = self._read_df(self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            return True
        df.loc[df["id"] == task_id, "done"] = "true" if done else "false"
        self._write_df(self.SHEET_CHECKLIST_TASKS, df, headers=["id", "topic_id", "texto", "done", "created_at"])
        return True

    def delete_checklist_task(self, task_id: str) -> bool:
        df = self._read_df(self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            return True
        df = df[df["id"] != task_id]
        self._write_df(self.SHEET_CHECKLIST_TASKS, df, headers=["id", "topic_id", "texto", "done", "created_at"])
        return True


def parse_spreadsheet_id(value: str) -> str:
    """Aceita ID puro ou URL do Google Sheets e retorna o Spreadsheet ID."""
    if not value:
        return ""
    s = str(value).strip()
    if "/spreadsheets/d/" in s:
        try:
            return s.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
        except Exception:
            return ""
    return s


def load_service_account_info_from_env_or_secrets(st_secrets: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Carrega o JSON do Service Account.

    Suporta:
      - GOOGLE_SERVICE_ACCOUNT_JSON (string JSON)
      - st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]
      - st.secrets["gcp_service_account"] (formato padrão do Streamlit)
    """

    env_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        try:
            return json.loads(env_json)
        except Exception as e:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON inválido no ambiente: " + str(e))

    if st_secrets:
        if "GOOGLE_SERVICE_ACCOUNT_JSON" in st_secrets and st_secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]:
            try:
                return json.loads(str(st_secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]))
            except Exception as e:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON inválido em secrets: " + str(e))

        if "gcp_service_account" in st_secrets and st_secrets["gcp_service_account"]:
            val = st_secrets["gcp_service_account"]
            if isinstance(val, dict):
                return val
            try:
                return json.loads(str(val))
            except Exception as e:
                raise ValueError("gcp_service_account inválido em secrets: " + str(e))

    raise ValueError(
        "Service account não configurado. Defina GOOGLE_SERVICE_ACCOUNT_JSON (string) ou gcp_service_account (dict) em Secrets."
    )
