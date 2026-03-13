import streamlit as st
import pandas as pd
import os
import subprocess
import time
from sqlalchemy.orm import Session
from app.db.models import Job

from app.storage.local_adapter import storage

def open_file(path: str):
    """Opens a file using the default OS application."""
    try:
        resolved_path = storage.resolve_path(path)
        if resolved_path and resolved_path.exists():
            os.startfile(str(resolved_path))
        else:
            st.error(f"Arquivo não encontrado: {path}")
            if resolved_path:
                st.caption(f"Caminho tentado: {resolved_path}")
    except Exception as e:
        st.error(f"Erro ao abrir arquivo: {e}")

def open_folder(path: str):
    """Opens the folder containing the file in Windows Explorer."""
    try:
        resolved_path = storage.resolve_path(path)
        if resolved_path and resolved_path.exists():
            subprocess.run(['explorer', '/select,', os.path.normpath(str(resolved_path))])
        else:
            st.error(f"Arquivo/Pasta não encontrada: {path}")
    except Exception as e:
        st.error(f"Erro ao abrir pasta: {e}")


STATUS_MAP = {
    "QUEUED": "Na Fila/Download",
    "STAGED": "Na Fila/Download",
    "UNKNOWN_DOC_TYPE": "Não mapeado",
    "FAILED": "Erro",
    "ERROR": "Erro"
}

STATUS_DESC = {
    "Erro": "Ocorreu um erro técnico ao baixar ou ler este arquivo.",
    "Não mapeado": "O documento não foi reconhecido por nenhum contrato, impedindo a tabulação.",
    "Concluído": "Processamento e extração de dados finalizados."
}

def render_dashboard(db: Session):
    st.title("📊 Dashboard de Documentos")
    
    # Explainer Expander
    with st.expander("ℹ️ Legenda de Status"):
        st.markdown("""
        **🔵 Resumo Simplificado**
        *   `Concluído`: Processamento de texto e extração finalizados (Mesmo com campos em branco).
        *   `Não mapeado`: O documento não correspondeu a nenhum tipo conhecido e a extração estruturada não ocorreu.
        *   `Erro`: Falha na infraestrutura (OCR, download ou API).
        """)

    # Metrics
    total_jobs = db.query(Job).count()
    pending_jobs = db.query(Job).filter(Job.status == "REVIEW_PENDING").count()
    processed_jobs = db.query(Job).filter(Job.status == "EXPORTED").count()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Documentos", total_jobs)
    c2.metric("Pendentes de Revisão", pending_jobs, delta_color="inverse")
    c3.metric("Finalizados / Exportados", processed_jobs)

    st.divider()

    # --- FILTROS AVANÇADOS ---
    st.subheader("🔍 Filtros e Pesquisa")
    
    # Filter Date (Generic)
    from datetime import datetime, timedelta
    col_d1, col_d2 = st.columns(2)
    start_date = col_d1.date_input("Data Inicial (E-mail)", value=datetime.now() - timedelta(days=30))
    end_date = col_d2.date_input("Data Final (E-mail)", value=datetime.now())

    expander = st.expander("Clique para expandir filtros por coluna", expanded=False)
    with expander:
        f1, f2, f3 = st.columns(3)
        
        # Reverse map for filter logic
        PT_TO_EN = {v: k for k, v in STATUS_MAP.items()}
        status_options = list(STATUS_MAP.values())
        
        curr_filter_default = ["REVISAO PENDENTE"]
        
        status_filter_pt = f1.multiselect(
            "Filtrar por Status", 
            status_options,
            default=[s for s in curr_filter_default if s in status_options]
        )
        
        # Convert selected PT statuses back to EN for query
        status_filter_en = [PT_TO_EN[s] for s in status_filter_pt]

        type_search = f2.text_input("Filtrar por Tipo (doc_type)")
        sender_search = f3.text_input("Filtrar por Remetente")
        
        f4, f5, f6 = st.columns(3)
        subject_search = f4.text_input("Pesquisar no Assunto")
        file_search = f5.text_input("Pesquisar no nome do Arquivo")
        id_search = f6.text_input("Filtrar por ID")

    # --- CONSTRUÇÃO DA QUERY ---
    query = db.query(Job)
    
    # Date Filter
    if start_date:
        query = query.filter(Job.email_date >= start_date)
    if end_date:
        # Inclusive end date (add 1 day approx or rely on time, usually dates have 00:00 time so <= checks same day 00:00, need to be careful)
        # Better to do < end_date + 1 day
        query = query.filter(Job.email_date < (end_date + timedelta(days=1)))

    if status_filter_en:
        query = query.filter(Job.status.in_(status_filter_en))
    if type_search:
        query = query.filter(Job.doc_type.ilike(f"%{type_search}%"))
    if sender_search:
        query = query.filter(Job.sender.ilike(f"%{sender_search}%"))
    if subject_search:
        query = query.filter(Job.subject.ilike(f"%{subject_search}%"))
    if file_search:
        query = query.filter(Job.attachment_name.ilike(f"%{file_search}%"))
    if id_search and id_search.isdigit():
        query = query.filter(Job.id == int(id_search))

    jobs = query.order_by(Job.created_at.desc()).limit(200).all()
    
    # Create DataFrame for display
    data = []
    for j in jobs:
        # Complex to Simple Mapping for internal UI matching:
        pt_status = "Em Processamento"
        if j.status in ["FAILED", "ERROR"]:
            pt_status = "Erro"
        elif j.status == "UNKNOWN_DOC_TYPE" or j.doc_type in ["UNKNOWN", "unknown", None]:
            pt_status = "Não mapeado"
        elif j.status in ["EXTRACTED", "VALIDATED", "COMPLETED", "APPROVED", "REVIEW_PENDING", "EXPORTED", "TEXT_EXTRACTED", "CLASSIFIED"]:
            pt_status = "Concluído"
        
        data.append({
            "ID": j.id,
            "Recebido em": j.email_date.strftime("%d/%m/%Y %H:%M") if j.email_date else "",
            "Remetente": j.sender,
            "Assunto": j.subject,
            "Arquivo": j.attachment_name,
            "Tipo": j.doc_type,
            "Confiança": f"{j.confidence*100:.1f}%" if j.confidence else "N/A",
            "Status": pt_status,
            "_path": j.storage_uri, # Hidden
            "_raw_status": j.status # Hidden for logic if needed
        })
    
    if data:
        df = pd.DataFrame(data)
        
        st.info("💡 Dica: Selecione várias linhas para aprovação em massa.")

        # Interactive Grid
        event = st.dataframe(
            df.drop(columns=["_path", "_raw_status"]), 
            width="stretch", 
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row", # ENABLE MULTI-ROW
            column_config={
                "ID": st.column_config.NumberColumn(format="%d"),
                "Confiança": st.column_config.TextColumn("Confiança"),
                "Status": st.column_config.TextColumn("Status"),
            }
        )
        
        # BULK ACTIONS
        selected_rows = event.selection.rows
        if len(selected_rows) > 0:
            st.divider()
            st.markdown(f"### ✨ Ações em Massa ({len(selected_rows)} selecionados)")
            
            # Get Selected IDs
            selected_ids = [df.iloc[idx]["ID"] for idx in selected_rows]
            
            c_act1, c_act2 = st.columns([1, 4])
            
            with c_act1:
                 if st.button("✅ Aprovar Selecionados", type="primary", use_container_width=True):
                    # Bulk Update
                    try:
                        db.query(Job).filter(Job.id.in_(selected_ids)).update(
                            {"status": "APPROVED"}, synchronize_session=False
                        )
                        db.commit()
                        st.success(f"{len(selected_ids)} registros aprovados com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na aprovação em massa: {e}")

            with c_act2:
                # Single Item Detailed View Logic (Show detail of FIRST selected item)
                if len(selected_ids) == 1:
                    first_idx = selected_rows[0]
                    first_row = df.iloc[first_idx]
                    
                    st.write(f"**Ações Individuais para #{first_row['ID']}:**")
                    
                    b1, b2, b3 = st.columns(3)
                    if b1.button("👁️ Ver Detalhes", key="btn_detail"):
                        st.session_state["selected_job_id"] = int(first_row["ID"])
                        st.rerun()
                        
                    if b2.button("📂 Abrir Arquivo", key="btn_open"):
                        open_file(first_row["_path"])
                        
                    if b3.button("📁 Abrir Pasta", key="btn_folder"):
                        open_folder(first_row["_path"])
            
    else:
        st.info("Nenhum job encontrado com os filtros atuais.")

