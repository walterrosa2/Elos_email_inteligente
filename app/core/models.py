from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class Origem(BaseModel):
    dt_email: datetime
    msg_id: str
    remetente: str
    assunto: str
    arquivo: str
    hash_arquivo: str
    caminho_original: str
    
    model_config = ConfigDict(extra='ignore')

class Erro(BaseModel):
    dt_email: datetime
    msg_id: str
    arquivo: str
    motivo: str
    detalhe: Optional[str] = ""
    acao_sugerida: Optional[str] = ""

    model_config = ConfigDict(extra='ignore')

class Cabecalho(BaseModel):
    dt_email: datetime
    msg_id: str
    tipo_nf: str
    chave: Optional[str] = None
    numero: Optional[str] = None
    serie: Optional[str] = None
    emissao: Optional[datetime] = None
    emitente_cnpj: Optional[str] = None
    emitente_razao: Optional[str] = None
    dest_cnpjcpf: Optional[str] = None
    dest_razao: Optional[str] = None
    valor_produtos: Optional[float] = 0.0
    valor_total: Optional[float] = 0.0
    icms_bc: Optional[float] = 0.0
    icms_valor: Optional[float] = 0.0
    ipi_valor: Optional[float] = 0.0
    pis_valor: Optional[float] = 0.0
    cofins_valor: Optional[float] = 0.0
    municipio: Optional[str] = None
    uf: Optional[str] = None
    forma_pagto: Optional[str] = None
    
    # Campo para armazenar dados extras que serão transformados em colunas EXTRA_*
    extra_campos: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra='allow') # Allowing extra fields to be passed easily if needed

class Item(BaseModel):
    chave: Optional[str] = None # Link com cabeçalho
    item_n: Optional[int] = None
    cod: Optional[str] = None
    descricao: Optional[str] = None
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    cst: Optional[str] = None
    un: Optional[str] = None
    qtde: Optional[float] = 0.0
    vlr_unit: Optional[float] = 0.0
    vlr_total: Optional[float] = 0.0
    icms_aliq: Optional[float] = 0.0
    icms_valor: Optional[float] = 0.0
    ipi_valor: Optional[float] = 0.0
    pis_valor: Optional[float] = 0.0
    cofins_valor: Optional[float] = 0.0
    
    extra_campos: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra='allow')
