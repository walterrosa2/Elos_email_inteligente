import streamlit as st
import base64
from sqlalchemy.orm import Session
from app.db.models import Job
from app.storage.local_adapter import storage
from app.contracts.manager import contract_manager

def render_job_detail(db: Session, job_id: int):
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        st.error("Job não encontrado.")
        if st.button("Voltar"):
            st.session_state["selected_job_id"] = None
            st.rerun()
        return

    st.button("← Voltar", on_click=lambda: st.session_state.update({"selected_job_id": None}))
    st.header(f"Revisão: {job.attachment_name}")
    
    col_pdf, col_form = st.columns([1, 1])
    
    # --- PDF Viewer ---
    # --- FILE VIEWER ---
    with col_pdf:
        st.subheader("Visualização")
        try:
            file_bytes = storage.get_file(job.storage_uri)
            
            # Determine file type
            fname = job.attachment_name.lower() if job.attachment_name else ""
            
            if fname.endswith(".pdf"):
                base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                
            elif fname.endswith((".txt", ".xml", ".json", ".csv", ".html", ".md", ".log")):
                # Refresh text content logic
                try:
                    text_content = file_bytes.decode("utf-8", errors="replace")
                    st.text_area("Conteúdo do Arquivo", value=text_content, height=600)
                except Exception as e:
                    st.error(f"Não foi possível decodificar o texto: {e}")
            
            elif fname.endswith((".png", ".jpg", ".jpeg")):
                st.image(file_bytes, caption=job.attachment_name)
                
            else:
                st.info(f"Visualização não disponível para este tipo de arquivo: {fname}")
                st.download_button("Baixar Arquivo", data=file_bytes, file_name=job.attachment_name)
                
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")

    # --- Edit Form ---
    with col_form:
        st.subheader("Dados Extraídos")
        
        # Document Type Selection
        contracts = contract_manager.list_contracts()
        contract_options = [c.doc_type for c in contracts]
        selected_type = st.selectbox("Tipo de Documento", contract_options, index=contract_options.index(job.doc_type) if job.doc_type in contract_options else 0)
        
        current_data = job.extraction_result if job.extraction_result else {}
        
        # Add "unknown" fields as raw JSON edition if type not set
        new_data = {}
        
        contract = contract_manager.get_contract(selected_type)
        if contract:
            with st.form("review_form"):
                st.info(f"Schema: {contract.description}")
                for field in contract.fields:
                    val = current_data.get(field.name, "")
                    new_val = st.text_input(f"{field.description} ({field.name})", value=str(val) if val is not None else "")
                    new_data[field.name] = new_val
                
                # Validation messages display
                if job.validation_errors:
                    st.warning("Erros de validação detectados anteriormente:")
                    for err in job.validation_errors:
                        st.write(f"- {err}")

                c1, c2 = st.columns(2)
                if c1.form_submit_button("✅ Aprovar Documento", type="primary"):
                    job.extraction_result = new_data
                    job.doc_type = selected_type
                    job.status = "APPROVED"
                    job.validation_errors = None # Clear errors on manual approval
                    db.commit()
                    st.success("Documento aprovado!")
                    st.session_state["selected_job_id"] = None
                    st.rerun()

                if c2.form_submit_button("❌ Rejeitar / Não Suportado"):
                    job.status = "FAILED"
                    job.validation_errors = ["Rejeitado manualmente pelo operador."]
                    db.commit()
                    st.error("Documento rejeitado.")
                    st.session_state["selected_job_id"] = None
                    st.rerun()
        else:
            st.warning("Selecione um tipo de documento válido para editar os campos.")

