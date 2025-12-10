from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class StatusEnum(str, Enum):
    """Enum para status de demandas"""
    TODO = "A Fazer"
    IN_PROGRESS = "Em Progresso"
    REVIEW = "Em Revisão"
    DONE = "Concluído"

class PriorityEnum(str, Enum):
    """Enum para prioridade de demandas"""
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    URGENTE = "Urgente"

@dataclass
class Etapa:
    """Modelo para etapas de um projeto"""
    id: str
    nome: str
    descricao: str = ""
    ordem: int = 0
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Demanda:
    """Modelo para demandas de projeto"""
    id: str
    titulo: str
    descricao: str
    projeto_id: str
    status: str = StatusEnum.TODO.value
    prioridade: str = PriorityEnum.MEDIA.value
    etapa_id: Optional[str] = None
    responsavel: Optional[str] = None
    data_inicio_plano: Optional[str] = None  # Data de início planejada
    data_inicio_real: Optional[str] = None   # Data de início real
    data_vencimento_plano: Optional[str] = None  # Data de vencimento planejada
    data_vencimento_real: Optional[str] = None   # Data de vencimento real (realizado)
    data_vencimento: Optional[str] = None  # Mantém para compatibilidade (será igual a plano)
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())
    data_conclusao: Optional[str] = None
    percentual_completo: int = 0  # 0-100
    tags: List[str] = field(default_factory=list)
    comentarios: List[str] = field(default_factory=list)
    
    def to_dict(self):
        data = asdict(self)
        return data
    
    @classmethod
    def from_dict(cls, data):
        # Ensure tags and comentarios are lists
        if 'tags' not in data:
            data['tags'] = []
        if 'comentarios' not in data:
            data['comentarios'] = []
        return cls(**data)

@dataclass
class Projeto:
    """Modelo para projetos"""
    id: str
    nome: str
    descricao: str = ""
    status: str = StatusEnum.TODO.value
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())
    data_conclusao: Optional[str] = None
    responsavel: Optional[str] = None
    etapas: List[Etapa] = field(default_factory=list)
    demandas: List[Demanda] = field(default_factory=list)
    
    def to_dict(self):
        data = asdict(self)
        data['etapas'] = [e.to_dict() if isinstance(e, Etapa) else e for e in self.etapas]
        data['demandas'] = [d.to_dict() if isinstance(d, Demanda) else d for d in self.demandas]
        return data
    
    @classmethod
    def from_dict(cls, data):
        etapas = [Etapa.from_dict(e) if isinstance(e, dict) else e for e in data.get('etapas', [])]
        demandas = [Demanda.from_dict(d) if isinstance(d, dict) else d for d in data.get('demandas', [])]
        data['etapas'] = etapas
        data['demandas'] = demandas
        return cls(**data)
