import json
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.db.database import SessionLocal, init_db
from app.db import models

class ContractField(BaseModel):
    name: str
    description: str
    type: str = "string"  # string, float, date, list
    required: bool = False

class Contract(BaseModel):
    doc_type: str
    version: str = "1.0"
    description: str
    fields: List[ContractField]
    keywords: List[str] = [] # For heuristic pre-filtering
    system_prompt: str # Instructions for the LLM
    
class ContractManager:
    def __init__(self, contracts_dir: str = "app/contracts/defaults"):
        self.contracts_dir = Path(contracts_dir)
        self.contracts: Dict[str, Contract] = {}
        init_db()  # ensure tables exist before querying
        self.reload_contracts()

    def reload_contracts(self):
        """Loads contracts from DB. Initializes DB from files if empty."""
        db = SessionLocal()
        try:
            # Check if we need to initialize
            if db.query(models.Contract).count() == 0:
                self._initialize_defaults(db)
            
            # Load from DB
            self.contracts = {}
            db_contracts = db.query(models.Contract).all()
            for db_c in db_contracts:
                fields = [
                    ContractField(
                        name=f.name,
                        description=f.description,
                        type=f.type,
                        required=f.required
                    ) for f in db_c.fields
                ]
                
                contract = Contract(
                    doc_type=db_c.doc_type,
                    version=db_c.version,
                    description=db_c.description or "",
                    fields=fields,
                    keywords=db_c.keywords or [],
                    system_prompt=db_c.system_prompt or ""
                )
                self.contracts[contract.doc_type] = contract
            
            logger.info(f"Loaded {len(self.contracts)} contracts from Database.")
            
        except Exception as e:
            logger.error(f"Error reloading contracts: {e}")
        finally:
            db.close()

    def _initialize_defaults(self, db: Session):
        logger.info("Initializing DB with default contracts from files...")
        if not self.contracts_dir.exists():
            logger.warning(f"Defaults directory {self.contracts_dir} not found.")
            return

        for file_path in self.contracts_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                # data matches the Pydantic/JSON structure. Need to map to DB models.
                
                db_contract = models.Contract(
                    doc_type=data["doc_type"],
                    version=data.get("version", "1.0"),
                    description=data.get("description", ""),
                    system_prompt=data.get("system_prompt", ""),
                    keywords=data.get("keywords", [])
                )
                db.add(db_contract)
                db.flush() # to get doc_type ready for FKs? Actually string PK, so ok.

                for f in data.get("fields", []):
                    db_field = models.ContractField(
                        contract_doc_type=db_contract.doc_type,
                        name=f["name"],
                        description=f["description"],
                        type=f.get("type", "string"),
                        required=f.get("required", False)
                    )
                    db.add(db_field)
                
                logger.info(f"Imported default contract: {data['doc_type']}")
            except Exception as e:
                logger.error(f"Failed to import default contract {file_path}: {e}")
        
        db.commit()

    def get_contract(self, doc_type: str) -> Optional[Contract]:
        # Optional: refresh from DB if not found? For now, cached.
        return self.contracts.get(doc_type)

    def list_contracts(self) -> List[Contract]:
        return list(self.contracts.values())

    def get_candidate_contracts(self, text: str) -> List[Contract]:
        """
        Returns a list of contracts that might match the text based on keywords.
        Pass all if no keywords defined or strict mode off.
        """
        candidates = []
        text_lower = text.lower()
        for contract in self.contracts.values():
            if not contract.keywords:
                candidates.append(contract)
                continue
            
            # Simple keyword match: if any keyword is present
            if any(k.lower() in text_lower for k in contract.keywords):
                candidates.append(contract)
        
        return candidates if candidates else list(self.contracts.values())
    
    def save_contract(self, contract_data: Contract):
        """Saves or updates a contract in the DB and reloads cache."""
        db = SessionLocal()
        try:
            # Check existing
            existing = db.query(models.Contract).filter(models.Contract.doc_type == contract_data.doc_type).first()
            if existing:
                db.delete(existing) # Simple replace strategy for now
                db.flush()
            
            new_contract = models.Contract(
                doc_type=contract_data.doc_type,
                version=contract_data.version,
                description=contract_data.description,
                system_prompt=contract_data.system_prompt,
                keywords=contract_data.keywords
            )
            db.add(new_contract)
            
            for f in contract_data.fields:
                new_field = models.ContractField(
                    contract_doc_type=new_contract.doc_type,
                    name=f.name,
                    description=f.description,
                    type=f.type,
                    required=f.required
                )
                db.add(new_field)
            
            db.commit()
            self.reload_contracts() # Refresh cache
            return True
        except Exception as e:
            logger.error(f"Failed to save contract {contract_data.doc_type}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

contract_manager = ContractManager()
