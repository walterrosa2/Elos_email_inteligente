from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class EmailContext(Base):
    __tablename__ = "email_contexts"

    message_id = Column(String, primary_key=True, index=True)
    subject = Column(String)
    sender = Column(String)
    received_at = Column(DateTime)
    body_text = Column(Text, nullable=True) # Full text content
    
    # Analysis Results
    analysis_date = Column(DateTime, nullable=True)
    criticality_score = Column(String) # e.g. "ALTA", "BAIXA"
    tone = Column(String) # e.g. "Agressivo", "Neutro"
    summary = Column(Text)
    action_required = Column(Boolean, default=False)
    
    raw_analysis_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_hash = Column(String(64), unique=True, index=True, nullable=False) # message_id + att_hash
    
    # Email Metadata
    message_id = Column(String, index=True)
    sender = Column(String)
    subject = Column(String)
    email_date = Column(DateTime)
    received_at = Column(DateTime, index=True)
    
    # Attachment Metadata
    attachment_name = Column(String)
    attachment_hash = Column(String)
    storage_uri = Column(String)
    
    # Processing Status
    status = Column(String, default="QUEUED", index=True) # QUEUED, STAGED, EXTRACTED, etc.
    doc_type = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Results
    textract_result = Column(JSON, nullable=True) # or path to json
    extraction_result = Column(JSON, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="operator") # admin, operator, auditor
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Contract(Base):
    __tablename__ = "contracts"

    doc_type = Column(String, primary_key=True, index=True)
    version = Column(String, default="1.0")
    description = Column(String)
    system_prompt = Column(String)
    keywords = Column(JSON) # List of strings stored as JSON
    
    # Relationship to fields
    fields = relationship("ContractField", back_populates="contract", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ContractField(Base):
    __tablename__ = "contract_fields"

    id = Column(Integer, primary_key=True, index=True)
    contract_doc_type = Column(String, ForeignKey("contracts.doc_type"))
    name = Column(String)
    description = Column(String)
    type = Column(String, default="string")
    required = Column(Boolean, default=False)

    contract = relationship("Contract", back_populates="fields")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(JSON) # Can store lists, dicts, strings
    description = Column(String)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
