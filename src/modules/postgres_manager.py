import ssl

from sqlalchemy import create_engine, Column, String, Integer, Text, JSON, text, delete as sa_delete
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
from src.modules.models import Projeto, Demanda, Etapa

Base = declarative_base()

class ProjetoModel(Base):
    __tablename__ = 'projetos'
    id = Column(String(64), primary_key=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)
    status = Column(String(50))
    responsavel = Column(String(255))
    data_criacao = Column(String(64))
    data_conclusao = Column(String(64))

class DemandaModel(Base):
    __tablename__ = 'demandas'
    id = Column(String(64), primary_key=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text)
    projeto_id = Column(String(64))
    status = Column(String(50))
    prioridade = Column(String(50))
    responsavel = Column(String(255))
    etapa_id = Column(String(64))
    data_inicio_plano = Column(String(64))
    data_inicio_real = Column(String(64))
    data_vencimento_plano = Column(String(64))
    data_vencimento_real = Column(String(64))
    data_vencimento = Column(String(64))
    data_criacao = Column(String(64))
    data_conclusao = Column(String(64))
    percentual_completo = Column(Integer)
    tags = Column(JSON)
    comentarios = Column(JSON)

class EtapaModel(Base):
    __tablename__ = 'etapas'
    id = Column(String(64), primary_key=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)
    ordem = Column(Integer)
    data_criacao = Column(String(64))

class PostgresManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.Session = None
        self.connected = False
        self.last_error = None

        # Try to create engine; normaliza driver para pg8000 e aplica SSL quando necessário
        try:
            engine, effective_url = self._create_engine(database_url)
            self.engine = engine
            # Create sessionmaker only if engine is created
            self.Session = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
            self.connected = True
            self.database_url = effective_url
        except Exception as e:
            # Store error; attempt a best-effort fallback
            self.last_error = e
            try:
                fallback_url = 'postgresql+pg8000://' + database_url.split('://', 1)[-1]
                engine, effective_url = self._create_engine(fallback_url)
                self.engine = engine
                self.Session = sessionmaker(bind=self.engine)
                Base.metadata.create_all(self.engine)
                self.connected = True
                self.database_url = effective_url
                self.last_error = None
            except Exception as e2:
                self.last_error = e2
                self.connected = False

    def _create_engine(self, database_url: str):
        """Cria engine SQLAlchemy para Postgres com pg8000.

        - Normaliza URLs do tipo postgresql:// para postgresql+pg8000://
        - Converte postgresql+psycopg2:// para postgresql+pg8000://
        - Trata sslmode/ssl em query string (comum em Neon/Supabase) e aplica ssl_context.
        """

        url = make_url(database_url)

        # Normalizar driver
        if url.drivername in {"postgresql", "postgres"}:
            url = url.set(drivername="postgresql+pg8000")
        elif url.drivername.startswith("postgresql+") and "pg8000" not in url.drivername:
            url = url.set(drivername="postgresql+pg8000")

        query = dict(url.query or {})

        sslmode = query.pop("sslmode", None)
        ssl_param = query.pop("ssl", None)
        # Parâmetro típico do libpq/psql; pg8000 não reconhece
        query.pop("channel_binding", None)

        need_ssl = False
        if sslmode is not None and str(sslmode).strip().lower() not in {"disable", "allow"}:
            need_ssl = True
        if ssl_param is not None and str(ssl_param).strip().lower() in {"1", "true", "yes", "require"}:
            need_ssl = True
        if url.host and url.host not in {"localhost", "127.0.0.1"}:
            need_ssl = True

        if query != dict(url.query or {}):
            url = url.set(query=query)

        connect_args = {}
        if need_ssl:
            connect_args["ssl_context"] = ssl.create_default_context()

        engine = create_engine(url, connect_args=connect_args)
        return engine, str(url)

    def load_projetos(self) -> List[Projeto]:
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        rows = session.query(ProjetoModel).all()
        projetos = []
        for r in rows:
            p = Projeto(
                id=r.id,
                nome=r.nome,
                descricao=r.descricao or '',
                status=r.status,
                data_criacao=r.data_criacao,
                data_conclusao=r.data_conclusao,
                responsavel=r.responsavel,
                etapas=[],
                demandas=[]
            )
            projetos.append(p)
        session.close()
        return projetos

    def save_projetos(self, projetos: List[Projeto]):
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        try:
            for p in projetos:
                model = session.get(ProjetoModel, p.id)
                if not model:
                    model = ProjetoModel(id=p.id)
                model.nome = p.nome
                model.descricao = p.descricao
                model.status = p.status
                model.responsavel = p.responsavel
                model.data_criacao = p.data_criacao
                model.data_conclusao = p.data_conclusao
                session.add(model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print('PostgresManager save_projetos error', e)
            return False
        finally:
            session.close()

    def load_demandas(self) -> List[Demanda]:
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        rows = session.query(DemandaModel).all()
        demandas = []
        for r in rows:
            d = Demanda(
                id=r.id,
                titulo=r.titulo,
                descricao=r.descricao,
                projeto_id=r.projeto_id,
                status=r.status,
                prioridade=r.prioridade,
                etapa_id=r.etapa_id,
                responsavel=r.responsavel,
                data_inicio_plano=r.data_inicio_plano,
                data_inicio_real=r.data_inicio_real,
                data_vencimento_plano=r.data_vencimento_plano,
                data_vencimento_real=r.data_vencimento_real,
                data_vencimento=r.data_vencimento,
                data_criacao=r.data_criacao,
                data_conclusao=r.data_conclusao,
                percentual_completo=r.percentual_completo or 0,
                tags=r.tags or [],
                comentarios=r.comentarios or []
            )
            demandas.append(d)
        session.close()
        return demandas

    def save_demandas(self, demandas: List[Demanda]):
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        try:
            for d in demandas:
                model = session.get(DemandaModel, d.id)
                if not model:
                    model = DemandaModel(id=d.id)
                model.titulo = d.titulo
                model.descricao = d.descricao
                model.projeto_id = d.projeto_id
                model.status = d.status
                model.prioridade = d.prioridade
                model.responsavel = d.responsavel
                model.etapa_id = d.etapa_id
                model.data_inicio_plano = d.data_inicio_plano
                model.data_inicio_real = d.data_inicio_real
                model.data_vencimento_plano = d.data_vencimento_plano
                model.data_vencimento_real = d.data_vencimento_real
                model.data_vencimento = d.data_vencimento
                model.data_criacao = d.data_criacao
                model.data_conclusao = d.data_conclusao
                model.percentual_completo = d.percentual_completo
                model.tags = d.tags
                model.comentarios = d.comentarios
                session.add(model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print('PostgresManager save_demandas error', e)
            return False
        finally:
            session.close()

    def load_etapas(self) -> List[Etapa]:
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        rows = session.query(EtapaModel).all()
        etapas = []
        for r in rows:
            e = Etapa(id=r.id, nome=r.nome, descricao=r.descricao, ordem=r.ordem, data_criacao=r.data_criacao)
            etapas.append(e)
        session.close()
        return etapas

    def save_etapas(self, etapas: List[Etapa]):
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        try:
            for e in etapas:
                model = session.get(EtapaModel, e.id)
                if not model:
                    model = EtapaModel(id=e.id)
                model.nome = e.nome
                model.descricao = e.descricao
                model.ordem = e.ordem
                model.data_criacao = e.data_criacao
                session.add(model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print('PostgresManager save_etapas error', e)
            return False
        finally:
            session.close()

    # ------------------------- Additional helpers -------------------------
    def health_check(self) -> bool:
        """Simple health check, executes SELECT 1 and returns True if OK."""
        if not self.connected:
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.last_error = e
            return False

    def delete_projeto(self, projeto_id: str) -> bool:
        """Delete a projeto by id from the database"""
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        try:
            obj = session.get(ProjetoModel, projeto_id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print('PostgresManager delete_projeto error', e)
            return False
        finally:
            session.close()

    def delete_demanda(self, demanda_id: str) -> bool:
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        try:
            obj = session.get(DemandaModel, demanda_id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print('PostgresManager delete_demanda error', e)
            return False
        finally:
            session.close()

    def delete_etapa(self, etapa_id: str) -> bool:
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        try:
            obj = session.get(EtapaModel, etapa_id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print('PostgresManager delete_etapa error', e)
            return False
        finally:
            session.close()

    def clear_all(self) -> bool:
        """Remove todos os registros das tabelas projetos, demandas e etapas."""
        if not self.connected:
            raise RuntimeError('PostgresManager not connected: ' + str(self.last_error))
        session = self.Session()
        try:
            # Prefer using DELETE for compatibility (works on SQLite and Postgres)
            session.execute(sa_delete(ProjetoModel))
            session.execute(sa_delete(DemandaModel))
            session.execute(sa_delete(EtapaModel))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print('PostgresManager clear_all error', e)
            return False
        finally:
            session.close()
