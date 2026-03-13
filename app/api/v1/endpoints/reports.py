from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import pandas as pd
import io
from typing import Optional
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.db.database import get_db
from app.db.models import Job
from app.api.security import get_current_user

router = APIRouter()

def sanitize_excel_value(value):
    """
    Prevents CSV/Excel formula injection by adding an apostrophe
    if the value starts with suspicious characters.
    """
    if value is None:
        return ""
    str_val = str(value)
    if str_val.startswith(('=', '+', '-', '@')):
        return f"'{str_val}"
    return str_val

@router.get("/export")
async def export_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    doc_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    subject: Optional[str] = None,
    filename: Optional[str] = None,
    criticality: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Export jobs/extractions to Excel (.xlsx) with multiple sheets and premium formatting.
    """
    from loguru import logger
    logger.info(f"Export requested by {current_user.username} with filters: start={start_date}, end={end_date}, status={status_filter}, doc={doc_type}, subject={subject}, file={filename}, crit={criticality}")
    
    # Join with EmailContext for criticality filter
    from app.db.models import EmailContext
    query = db.query(Job, EmailContext.criticality_score).outerjoin(
        EmailContext, Job.message_id == EmailContext.message_id
    )
    
    # 1. Apply Filters
    if start_date:
        query = query.filter(Job.received_at >= start_date)
            
    if end_date:
        from datetime import time
        dt_end_full = datetime.combine(end_date.date(), time(23, 59, 59, 999999))
        query = query.filter(Job.received_at <= dt_end_full)
            
    if doc_type:
        query = query.filter(Job.doc_type == doc_type)
        
    if subject:
        query = query.filter(Job.subject.ilike(f"%{subject}%"))
        
    if filename:
        query = query.filter(Job.attachment_name.ilike(f"%{filename}%"))
        
    if criticality:
        query = query.filter(EmailContext.criticality_score == criticality)

    if status_filter:
        if status_filter == "Concluído":
            query = query.filter(Job.status.in_(["EXTRACTED", "VALIDATED", "COMPLETED", "APPROVED", "REVIEW_PENDING", "EXPORTED"]))
            query = query.filter(Job.doc_type.isnot(None), Job.doc_type != "UNKNOWN", Job.doc_type != "unknown")
        elif status_filter == "Não mapeado":
            query = query.filter(or_(
                Job.status == "UNKNOWN_DOC_TYPE", 
                Job.doc_type == "UNKNOWN", 
                Job.doc_type == "unknown",
                Job.doc_type.is_(None)
            ))
        elif status_filter == "Erro":
            query = query.filter(Job.status.in_(["ERROR", "FAILED"]))
        else:
            query = query.filter(Job.status == status_filter)
        
    jobs_tuples = query.order_by(Job.received_at.desc()).all()
    jobs = [t[0] for t in jobs_tuples]
    
    # 2. Prepare Data Frames
    # Sheet 1: General Data
    general_data = []
    for job in jobs:
        # Simplified status logic for Excel
        if job.status in ["ERROR", "FAILED"]:
            sim_status = "Erro"
        elif job.status == "UNKNOWN_DOC_TYPE" or job.doc_type in ["UNKNOWN", "unknown", None]:
            sim_status = "Não mapeado"
        else:
            sim_status = "Concluído"

        general_data.append({
            "ID": job.id,
            "Data Recebimento": job.received_at.strftime("%d/%m/%Y %H:%M") if job.received_at else "",
            "Remetente": sanitize_excel_value(job.sender),
            "Assunto": sanitize_excel_value(job.subject),
            "Arquivo": sanitize_excel_value(job.attachment_name),
            "Tipo": job.doc_type or "N/A",
            "Status": sim_status,
            "Confiança %": f"{int((job.confidence or 0) * 100)}%"
        })
    df_general = pd.DataFrame(general_data)

    # Dictionary to hold dataframes for each doc_type
    sheets_by_contract = {}
    
    for job in jobs:
        if not job.doc_type or job.doc_type == "UNKNOWN":
            continue
            
        if job.doc_type not in sheets_by_contract:
            sheets_by_contract[job.doc_type] = []
            
        row = {"Job ID": job.id}
        if job.extraction_result and isinstance(job.extraction_result, dict):
            # Flatten extraction_result
            def flatten(d, parent_key='', sep='_'):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, sanitize_excel_value(v)))
                return dict(items)
            
            flat_res = flatten(job.extraction_result)
            row.update(flat_res)
        
        sheets_by_contract[job.doc_type].append(row)

    # 3. Write Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write general sheet
        df_general.to_excel(writer, index=False, sheet_name='Visão Geral')
        
        # Write contract specific sheets
        for c_type, c_data in sheets_by_contract.items():
            df_contract = pd.DataFrame(c_data)
            df_contract.to_excel(writer, index=False, sheet_name=c_type[:30]) # Excel limit 31 chars
            
        # 4. Premium Formatting
        workbook = writer.book
        header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
        header_font = Font(color='FFFFFF', bold=True)
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        for sheet in workbook.worksheets:
            # Format header
            for cell in sheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = thin_border
            
            # Freeze header row
            sheet.freeze_panes = 'A2'
            
            # Auto-adjust column width
            for col in sheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                sheet.column_dimensions[column].width = min(adjusted_width, 50) # Cap at 50

    output.seek(0)
    filename = f"Relatorio_ELOS_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
