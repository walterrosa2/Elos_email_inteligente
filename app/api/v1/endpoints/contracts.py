from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Contract, ContractField
from app.api.schemas import schemas
from app.api.security import get_admin_user

router = APIRouter()

@router.get("", response_model=List[schemas.ContractResponse])
def list_contracts(db: Session = Depends(get_db), current_admin=Depends(get_admin_user)):
    return db.query(Contract).all()

@router.get("/{doc_type}", response_model=schemas.ContractResponse)
def get_contract(doc_type: str, db: Session = Depends(get_db), current_admin=Depends(get_admin_user)):
    contract = db.query(Contract).filter(Contract.doc_type == doc_type).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.put("/{doc_type}", response_model=schemas.ContractResponse)
def update_contract(
    doc_type: str, 
    contract_in: schemas.ContractBase, 
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    contract = db.query(Contract).filter(Contract.doc_type == doc_type).first()
    if not contract:
         raise HTTPException(status_code=404, detail="Contract not found")
         
    in_data = contract_in.model_dump(exclude={"fields"})
    for key, value in in_data.items():
        setattr(contract, key, value)
        
    if contract_in.fields is not None:
        # Clear existing
        db.query(ContractField).filter(ContractField.contract_doc_type == doc_type).delete()
        # Add new
        for f in contract_in.fields:
            new_field = ContractField(**f.model_dump(), contract_doc_type=doc_type)
            db.add(new_field)
        
    db.commit()
    db.refresh(contract)
    return contract

@router.post("/", response_model=schemas.ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_in: schemas.ContractBase,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    contract = db.query(Contract).filter(Contract.doc_type == contract_in.doc_type).first()
    if contract:
        raise HTTPException(status_code=400, detail="Contract already exists for this doc_type")
        
    in_data = contract_in.model_dump(exclude={"fields"})
    new_contract = Contract(**in_data)
    db.add(new_contract)
    
    if contract_in.fields:
        for f in contract_in.fields:
            new_field = ContractField(**f.model_dump(), contract_doc_type=contract_in.doc_type)
            db.add(new_field)
            
    db.commit()
    db.refresh(new_contract)
    return new_contract
