from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime

# --- Generic Responses ---

class MessageResponse(BaseModel):
    message: str

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int

# --- Email Contexts ---

class EmailContextBase(BaseModel):
    message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    received_at: Optional[datetime] = None
    body_text: Optional[str] = None

class EmailContextResponse(EmailContextBase):
    analysis_date: Optional[datetime] = None
    criticality_score: Optional[str] = None
    tone: Optional[str] = None
    summary: Optional[str] = None
    action_required: bool = False
    raw_analysis_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Jobs ---

class JobBase(BaseModel):
    message_id: Optional[str] = None
    sender: Optional[str] = None
    subject: Optional[str] = None
    attachment_name: Optional[str] = None

class JobResponse(JobBase):
    id: int
    job_hash: str
    email_date: Optional[datetime] = None
    received_at: Optional[datetime] = None
    status: str
    doc_type: Optional[str] = None
    confidence: Optional[float] = None
    storage_uri: Optional[str] = None
    extraction_result: Optional[Dict[str, Any]] = None
    validation_errors: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class JobUpdateExtraction(BaseModel):
    extraction_result: Dict[str, Any]

class JobBulkApprove(BaseModel):
    ids: List[int]

class JobStatItem(BaseModel):
    label: str
    count: int

class JobStats(BaseModel):
    status_distribution: List[JobStatItem]
    doc_type_distribution: List[JobStatItem]
    daily_volume: List[JobStatItem]

class JobSummary(BaseModel):
    id: int
    status: str
    simplified_status: str  # Concluído, Não mapeado, Erro
    sender: Optional[str] = None
    subject: Optional[str] = None
    attachment_name: Optional[str] = None
    received_at: Optional[datetime] = None
    doc_type: Optional[str] = None
    confidence: Optional[float] = None
    criticality: Optional[str] = None
    extraction_result: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

# --- Users ---

class UserBase(BaseModel):
    username: str
    role: str = "elos" # admin, elos

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# --- Contracts ---

class ContractFieldBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "string"
    required: bool = False

class ContractFieldResponse(ContractFieldBase):
    id: int
    contract_doc_type: str

    model_config = ConfigDict(from_attributes=True)

class ContractBase(BaseModel):
    doc_type: str
    version: str = "1.0"
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    keywords: Optional[List[str]] = None
    fields: Optional[List[ContractFieldBase]] = []

class ContractResponse(ContractBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    fields: List[ContractFieldResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- System Settings ---

class SystemSettingBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

class SystemSettingResponse(SystemSettingBase):
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ScheduleConfig(BaseModel):
    enabled: bool = False
    interval_minutes: int = 60
    start_time: str = "08:00" # HH:mm
    end_time: str = "20:00" # HH:mm
    days_of_week: List[int] = [0, 1, 2, 3, 4] # 0=Mon, 6=Sun
