from sqlalchemy import create_engine, Column, String, Integer, Text, JSON
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
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.connected = True

    def load_projetos(self) -> List[Projeto]:
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
        session = self.Session()
        rows = session.query(EtapaModel).all()
        etapas = []
        for r in rows:
            e = Etapa(id=r.id, nome=r.nome, descricao=r.descricao, ordem=r.ordem, data_criacao=r.data_criacao)
            etapas.append(e)
        session.close()
        return etapas

    def save_etapas(self, etapas: List[Etapa]):
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
