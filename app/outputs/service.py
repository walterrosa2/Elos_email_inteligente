import pandas as pd
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Job

class OutputService:
    def __init__(self, db: Session):
        self.db = db

    def generate_excel_report(self, start_date: datetime = None, end_date: datetime = None) -> bytes:
        """
        Generates an Excel file with all Jobs in the period.
        Creates separate sheets for each Contract Type (doc_type) with specific columns.
        Also includes a 'Geral' sheet for summary.
        """
        from app.contracts.manager import contract_manager # Import here to avoid circular dependency if any
        
        query = self.db.query(Job)
        
        if start_date:
            query = query.filter(Job.created_at >= start_date)
        if end_date:
            query = query.filter(Job.created_at <= end_date)
            
        jobs = query.all()
        
        # 1. Prepare General Data
        general_rows = []
        jobs_by_type = {} # Key: doc_type, Value: list[Job]
        
        for job in jobs:
            # Retrieve Email Context
            from app.db.models import EmailContext
            context = self.db.query(EmailContext).filter(EmailContext.message_id == job.message_id).first()
            
            crit = context.criticality_score if context else ""
            tone = context.tone if context else ""
            summary = context.summary if context else ""
            
            # Add to General list
            row_general = {
                "Job ID": job.id,
                "Status": job.status,
                "Data E-mail": job.email_date,
                "[Email] Criticidade": crit,
                "[Email] Tom": tone,
                "[Email] Resumo": summary,
                "Remetente": job.sender,
                "Assunto": job.subject,
                "Arquivo": job.attachment_name,
                "Tipo Doc": job.doc_type,
                "Confiança": job.confidence,
                "Erros": str(job.validation_errors) if job.validation_errors else ""
            }
            general_rows.append(row_general)
            
            # Group by Type
            if job.doc_type:
                if job.doc_type not in jobs_by_type:
                    jobs_by_type[job.doc_type] = []
                jobs_by_type[job.doc_type].append(job)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Geral
            df_general = pd.DataFrame(general_rows)
            # Ensure basic columns exist even if empty
            if df_general.empty:
                df_general = pd.DataFrame(columns=["Job ID", "Status", "Data E-mail", "Remetente", "Assunto", "Arquivo", "Tipo Doc"])
            df_general.to_excel(writer, index=False, sheet_name="Relatorio_Geral")
            
            # Sheet N: Per Contract
            active_contracts = contract_manager.list_contracts()
            
            for contract in active_contracts:
                doc_type_key = contract.doc_type
                if doc_type_key in jobs_by_type:
                    # Prepare rows for this specific contract
                    contract_jobs = jobs_by_type[doc_type_key]
                    contract_rows = []
                    
                    # Get fields defined in schema to order columns nicely
                    schema_fields = [f.name for f in contract.fields]
                    
                    for c_job in contract_jobs:
                        # Base info
                        c_row = {
                            "ID": c_job.id,
                            "Data": c_job.email_date,
                            "Arquivo": c_job.attachment_name,
                            "Status": c_job.status
                        }
                        
                        # Extracted data
                        extracted = c_job.extraction_result if c_job.extraction_result else {}
                        
                        # Fill schema fields
                        for field in schema_fields:
                            c_row[field] = extracted.get(field, "")
                            
                        contract_rows.append(c_row)
                    
                    df_contract = pd.DataFrame(contract_rows)
                    # Sheet name max 31 chars
                    safe_sheet_name = doc_type_key[:30].replace("/", "-") 
                    df_contract.to_excel(writer, index=False, sheet_name=safe_sheet_name)
            
            # Catch-all for types not in active contracts but present in DB (legacy?)
            # (Optional improvement, skipping for now to keep it clean)
            
        return output.getvalue()

    def export_jsons(self, output_dir: str):
        """
        Exports individual JSON files for legacy integration.
        """
        # Implementation placeholder / example
        pass

