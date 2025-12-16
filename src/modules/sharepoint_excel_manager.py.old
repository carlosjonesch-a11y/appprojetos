import json
from dataclasses import asdict
from datetime import datetime
from io import BytesIO
from typing import List, Optional
from urllib.parse import quote

import pandas as pd
import requests
import msal

from src.modules.models import Projeto, Demanda, Etapa


class SharePointExcelManager:
    """Persistência em um único arquivo .xlsx no SharePoint via Microsoft Graph.

    Observação: este backend faz download -> altera -> upload do arquivo inteiro.
    Para o volume deste app (centenas de linhas), costuma ser suficiente.
    """

    SHEET_PROJETOS = "projetos"
    SHEET_DEMANDAS = "demandas"
    SHEET_ETAPAS = "etapas"
    SHEET_CHECKLIST_TOPICS = "checklist_topics"
    SHEET_CHECKLIST_TASKS = "checklist_tasks"

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        site_host: str,
        site_path: str,
        file_path: str,
        timeout_seconds: int = 30,
    ):
        self.tenant_id = (tenant_id or "").strip()
        self.client_id = (client_id or "").strip()
        self.client_secret = (client_secret or "").strip()
        self.site_host = (site_host or "").strip()
        self.site_path = (site_path or "").strip()
        self.file_path = (file_path or "").strip().lstrip("/")
        self.timeout_seconds = timeout_seconds

        self.connected = False
        self.last_error: Optional[Exception] = None

        self._cached_site_id: Optional[str] = None
        self._cached_item_id: Optional[str] = None

        # compat com partes do app que esperam esse atributo
        self.database_url = "sharepoint://excel"

        try:
            self.connected = self.health_check()
        except Exception as exc:
            self.connected = False
            self.last_error = exc

    # ------------------------- Graph helpers -------------------------
    def _get_token(self) -> str:
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret,
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError(f"Falha ao obter token do Graph: {result.get('error')}: {result.get('error_description')}")
        return result["access_token"]

    def _graph(self, method: str, url: str, token: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        return requests.request(method, url, headers=headers, timeout=self.timeout_seconds, **kwargs)

    def _resolve_site_id(self, token: str) -> str:
        if self._cached_site_id:
            return self._cached_site_id

        if not self.site_path.startswith("/"):
            site_path = "/" + self.site_path
        else:
            site_path = self.site_path

        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_host}:{site_path}"
        resp = self._graph("GET", url, token)
        if resp.status_code >= 400:
            raise RuntimeError(f"Erro ao resolver site_id: {resp.status_code} {resp.text}")
        self._cached_site_id = resp.json()["id"]
        return self._cached_site_id

    def _resolve_item_id(self, token: str) -> str:
        if self._cached_item_id:
            return self._cached_item_id

        site_id = self._resolve_site_id(token)
        encoded_path = quote(self.file_path)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{encoded_path}"
        resp = self._graph("GET", url, token)
        if resp.status_code == 404:
            # arquivo não existe ainda
            self._cached_item_id = ""
            return ""
        if resp.status_code >= 400:
            raise RuntimeError(f"Erro ao resolver item_id: {resp.status_code} {resp.text}")
        self._cached_item_id = resp.json()["id"]
        return self._cached_item_id

    def _download_workbook_bytes(self, token: str) -> bytes:
        site_id = self._resolve_site_id(token)
        item_id = self._resolve_item_id(token)
        if not item_id:
            raise FileNotFoundError("Arquivo .xlsx não encontrado no SharePoint")

        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{item_id}/content"
        resp = self._graph("GET", url, token, allow_redirects=True)
        if resp.status_code >= 400:
            raise RuntimeError(f"Erro ao baixar arquivo: {resp.status_code} {resp.text}")
        return resp.content

    def _upload_workbook_bytes(self, token: str, content: bytes) -> bool:
        site_id = self._resolve_site_id(token)
        item_id = self._resolve_item_id(token)

        if item_id:
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{item_id}/content"
        else:
            # cria arquivo novo
            encoded_path = quote(self.file_path)
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{encoded_path}:/content"

        resp = self._graph(
            "PUT",
            url,
            token,
            data=content,
            headers={"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Erro ao enviar arquivo: {resp.status_code} {resp.text}")

        # re-resolve id se foi criado
        self._cached_item_id = resp.json().get("id") or self._cached_item_id
        return True

    # ------------------------- Excel helpers -------------------------
    def _empty_workbook_bytes(self) -> bytes:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame(columns=["id", "nome", "descricao", "status", "responsavel", "data_criacao", "data_conclusao"]).to_excel(
                writer, sheet_name=self.SHEET_PROJETOS, index=False
            )
            pd.DataFrame(
                columns=[
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
            ).to_excel(writer, sheet_name=self.SHEET_DEMANDAS, index=False)
            pd.DataFrame(columns=["id", "nome", "descricao", "ordem", "data_criacao"]).to_excel(writer, sheet_name=self.SHEET_ETAPAS, index=False)
            pd.DataFrame(columns=["id", "nome", "data_criacao"]).to_excel(writer, sheet_name=self.SHEET_CHECKLIST_TOPICS, index=False)
            pd.DataFrame(columns=["id", "topic_id", "texto", "concluida", "data_criacao"]).to_excel(writer, sheet_name=self.SHEET_CHECKLIST_TASKS, index=False)

        return output.getvalue()

    def _ensure_workbook(self, token: str) -> None:
        try:
            _ = self._download_workbook_bytes(token)
        except FileNotFoundError:
            content = self._empty_workbook_bytes()
            self._upload_workbook_bytes(token, content)

    def _read_sheet(self, wb_bytes: bytes, sheet: str) -> pd.DataFrame:
        bio = BytesIO(wb_bytes)
        try:
            df = pd.read_excel(bio, sheet_name=sheet, engine="openpyxl")
            if df is None:
                return pd.DataFrame()
            return df
        except ValueError:
            # sheet não existe
            return pd.DataFrame()

    def _write_sheets(self, token: str, frames: dict[str, pd.DataFrame]) -> bool:
        # baixa para preservar sheets não tocadas
        self._ensure_workbook(token)
        existing = self._download_workbook_bytes(token)

        # carrega todos os sheets existentes
        bio = BytesIO(existing)
        try:
            xls = pd.ExcelFile(bio, engine="openpyxl")
            existing_sheets = {name: pd.read_excel(bio, sheet_name=name, engine="openpyxl") for name in xls.sheet_names}
        except Exception:
            existing_sheets = {}

        # sobrescreve os frames fornecidos
        for name, df in frames.items():
            existing_sheets[name] = df

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for name, df in existing_sheets.items():
                df.to_excel(writer, sheet_name=name, index=False)

            # garante as sheets principais
            for required in [
                self.SHEET_PROJETOS,
                self.SHEET_DEMANDAS,
                self.SHEET_ETAPAS,
                self.SHEET_CHECKLIST_TOPICS,
                self.SHEET_CHECKLIST_TASKS,
            ]:
                if required not in existing_sheets:
                    pd.DataFrame().to_excel(writer, sheet_name=required, index=False)

        return self._upload_workbook_bytes(token, output.getvalue())

    # ------------------------- Public API (compat com PostgresManager) -------------------------
    def health_check(self) -> bool:
        try:
            token = self._get_token()
            self._ensure_workbook(token)
            # tenta baixar
            _ = self._download_workbook_bytes(token)
            return True
        except Exception as exc:
            self.last_error = exc
            return False

    def load_projetos(self) -> List[Projeto]:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_PROJETOS)
        if df.empty:
            return []
        df = df.fillna("")
        projetos: List[Projeto] = []
        for _, r in df.iterrows():
            projetos.append(
                Projeto(
                    id=str(r.get("id", "")),
                    nome=str(r.get("nome", "")),
                    descricao=str(r.get("descricao", "")),
                    status=str(r.get("status", "")) or "Ativo",
                    responsavel=str(r.get("responsavel", "")) or "",
                    data_criacao=str(r.get("data_criacao", "")) or datetime.now().strftime("%Y-%m-%d"),
                    data_conclusao=str(r.get("data_conclusao", "")) or None,
                    etapas=[],
                    demandas=[],
                )
            )
        return projetos

    def save_projetos(self, projetos: List[Projeto]) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        rows = []
        for p in projetos:
            d = asdict(p)
            d.pop("etapas", None)
            d.pop("demandas", None)
            rows.append(d)
        df = pd.DataFrame(rows)
        return self._write_sheets(token, {self.SHEET_PROJETOS: df})

    def load_etapas(self) -> List[Etapa]:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_ETAPAS)
        if df.empty:
            return []
        etapas: List[Etapa] = []
        for _, r in df.iterrows():
            try:
                ordem = int(r.get("ordem")) if not pd.isna(r.get("ordem")) else 0
            except Exception:
                ordem = 0
            etapas.append(
                Etapa(
                    id=str(r.get("id", "")),
                    nome=str(r.get("nome", "")),
                    descricao=str(r.get("descricao", "")) if not pd.isna(r.get("descricao")) else "",
                    ordem=ordem,
                    data_criacao=str(r.get("data_criacao", "")) if not pd.isna(r.get("data_criacao")) else datetime.now().strftime("%Y-%m-%d"),
                )
            )
        return etapas

    def save_etapas(self, etapas: List[Etapa]) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        df = pd.DataFrame([asdict(e) for e in etapas])
        return self._write_sheets(token, {self.SHEET_ETAPAS: df})

    def _parse_json_list(self, value) -> list:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                # fallback simples
                return [x.strip() for x in s.split(",") if x.strip()]
        return []

    def load_demandas(self) -> List[Demanda]:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_DEMANDAS)
        if df.empty:
            return []

        demandas: List[Demanda] = []
        for _, r in df.iterrows():
            try:
                pct = int(r.get("percentual_completo")) if not pd.isna(r.get("percentual_completo")) else 0
            except Exception:
                pct = 0

            demandas.append(
                Demanda(
                    id=str(r.get("id", "")),
                    titulo=str(r.get("titulo", "")),
                    descricao=str(r.get("descricao", "")) if not pd.isna(r.get("descricao")) else "",
                    projeto_id=str(r.get("projeto_id", "")),
                    status=str(r.get("status", "")) or "A Fazer",
                    prioridade=str(r.get("prioridade", "")) or "Média",
                    etapa_id=str(r.get("etapa_id", "")) if not pd.isna(r.get("etapa_id")) else None,
                    responsavel=str(r.get("responsavel", "")) if not pd.isna(r.get("responsavel")) else None,
                    data_inicio_plano=str(r.get("data_inicio_plano", "")) if not pd.isna(r.get("data_inicio_plano")) else None,
                    data_inicio_real=str(r.get("data_inicio_real", "")) if not pd.isna(r.get("data_inicio_real")) else None,
                    data_vencimento_plano=str(r.get("data_vencimento_plano", "")) if not pd.isna(r.get("data_vencimento_plano")) else None,
                    data_vencimento_real=str(r.get("data_vencimento_real", "")) if not pd.isna(r.get("data_vencimento_real")) else None,
                    data_vencimento=str(r.get("data_vencimento", "")) if not pd.isna(r.get("data_vencimento")) else None,
                    data_criacao=str(r.get("data_criacao", "")) if not pd.isna(r.get("data_criacao")) else datetime.now().strftime("%Y-%m-%d"),
                    data_conclusao=str(r.get("data_conclusao", "")) if not pd.isna(r.get("data_conclusao")) else None,
                    percentual_completo=pct,
                    tags=self._parse_json_list(r.get("tags")),
                    comentarios=self._parse_json_list(r.get("comentarios")),
                )
            )
        return demandas

    def save_demandas(self, demandas: List[Demanda]) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        rows = []
        for d in demandas:
            payload = asdict(d)
            payload["tags"] = json.dumps(payload.get("tags") or [], ensure_ascii=False)
            payload["comentarios"] = json.dumps(payload.get("comentarios") or [], ensure_ascii=False)
            rows.append(payload)
        df = pd.DataFrame(rows)
        return self._write_sheets(token, {self.SHEET_DEMANDAS: df})

    def delete_projeto(self, projeto_id: str) -> bool:
        projetos = [p for p in self.load_projetos() if p.id != projeto_id]
        return self.save_projetos(projetos)

    def delete_demanda(self, demanda_id: str) -> bool:
        demandas = [d for d in self.load_demandas() if d.id != demanda_id]
        return self.save_demandas(demandas)

    def delete_etapa(self, etapa_id: str) -> bool:
        etapas = [e for e in self.load_etapas() if e.id != etapa_id]
        return self.save_etapas(etapas)

    def clear_all(self) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        return self._write_sheets(
            token,
            {
                self.SHEET_PROJETOS: pd.DataFrame(),
                self.SHEET_DEMANDAS: pd.DataFrame(),
                self.SHEET_ETAPAS: pd.DataFrame(),
                self.SHEET_CHECKLIST_TOPICS: pd.DataFrame(),
                self.SHEET_CHECKLIST_TASKS: pd.DataFrame(),
            },
        )

    def clear_core_data(self) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        return self._write_sheets(
            token,
            {
                self.SHEET_PROJETOS: pd.DataFrame(),
                self.SHEET_DEMANDAS: pd.DataFrame(),
                self.SHEET_ETAPAS: pd.DataFrame(),
            },
        )

    # ------------------------- Checklist helpers -------------------------
    def load_checklist_topics(self) -> list[dict]:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_CHECKLIST_TOPICS)
        if df.empty:
            return []
        df = df.fillna("")
        rows = []
        for _, r in df.iterrows():
            if not str(r.get("id", "")).strip():
                continue
            rows.append({"id": str(r.get("id")), "nome": str(r.get("nome", "")), "data_criacao": str(r.get("data_criacao", ""))})
        rows.sort(key=lambda x: x.get("data_criacao", ""))
        return rows

    def create_checklist_topic(self, topic_id: str, nome: str, data_criacao: str) -> bool:
        topics = self.load_checklist_topics()
        topics.append({"id": topic_id, "nome": nome, "data_criacao": data_criacao})
        df = pd.DataFrame(topics)
        token = self._get_token()
        self._ensure_workbook(token)
        return self._write_sheets(token, {self.SHEET_CHECKLIST_TOPICS: df})

    def rename_checklist_topic(self, topic_id: str, novo_nome: str) -> bool:
        topics = self.load_checklist_topics()
        found = False
        for t in topics:
            if t.get("id") == topic_id:
                t["nome"] = novo_nome
                found = True
                break
        if not found:
            return False
        df = pd.DataFrame(topics)
        token = self._get_token()
        self._ensure_workbook(token)
        return self._write_sheets(token, {self.SHEET_CHECKLIST_TOPICS: df})

    def load_checklist_tasks(self, topic_id: str) -> list[dict]:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            return []

        tasks = []
        for _, r in df.iterrows():
            if str(r.get("topic_id", "")) != str(topic_id):
                continue
            concluida = False
            v = r.get("concluida")
            if isinstance(v, bool):
                concluida = v
            else:
                try:
                    if pd.isna(v):
                        concluida = False
                    else:
                        concluida = bool(int(v)) if str(v).strip().isdigit() else str(v).strip().lower() in {"true", "sim", "yes", "1"}
                except Exception:
                    concluida = False

            tasks.append(
                {
                    "id": str(r.get("id")),
                    "topic_id": str(r.get("topic_id")),
                    "texto": str(r.get("texto", "")) if not pd.isna(r.get("texto")) else "",
                    "concluida": bool(concluida),
                    "data_criacao": str(r.get("data_criacao", "")) if not pd.isna(r.get("data_criacao")) else "",
                }
            )

        tasks.sort(key=lambda x: x.get("data_criacao", ""))
        return tasks

    def create_checklist_task(self, task_id: str, topic_id: str, texto: str, data_criacao: str) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            tasks = []
        else:
            tasks = df.fillna("").to_dict("records")

        tasks.append({"id": task_id, "topic_id": topic_id, "texto": texto, "concluida": False, "data_criacao": data_criacao})
        out_df = pd.DataFrame(tasks)
        return self._write_sheets(token, {self.SHEET_CHECKLIST_TASKS: out_df})

    def set_checklist_task_done(self, task_id: str, done: bool) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            return False
        df = df.copy()
        df["id"] = df["id"].astype(str)
        df.loc[df["id"] == str(task_id), "concluida"] = bool(done)
        return self._write_sheets(token, {self.SHEET_CHECKLIST_TASKS: df})

    def delete_checklist_task(self, task_id: str) -> bool:
        token = self._get_token()
        self._ensure_workbook(token)
        wb = self._download_workbook_bytes(token)
        df = self._read_sheet(wb, self.SHEET_CHECKLIST_TASKS)
        if df.empty:
            return True
        df = df.copy()
        df["id"] = df["id"].astype(str)
        df = df[df["id"] != str(task_id)]
        return self._write_sheets(token, {self.SHEET_CHECKLIST_TASKS: df})
