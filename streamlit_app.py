import streamlit as st
from datetime import datetime
from app.core.config import settings
from app.db.database import SessionLocal, init_db
from app.review.auth import init_auth, logout
from app.review.dashboard import render_dashboard
from app.review.detail import render_job_detail
from app.orchestrator.pipeline import PipelineOrchestrator
from app.ingest.service import IngestionService

# Ensure tables exist
init_db()

st.set_page_config(page_title="Pipeline V2.1 - Review", layout="wide")

# Initialize Auth
if not init_auth():
    st.stop()

# Sidebar
from app.outputs.service import OutputService
from app.observability.dashboard import render_observability

st.sidebar.title(f"👤 {st.session_state['username']}")
if st.sidebar.button("Sair", key="logout_btn"):
    logout()

st.sidebar.divider()
menu = st.sidebar.radio("Navegação", ["Dashboard", "Execução Manual", "Gestão de Contratos", "Análise de E-mail", "Relatórios", "Auditoria", "Configurações"])

db = SessionLocal()

try:
    if "selected_job_id" not in st.session_state:
        st.session_state["selected_job_id"] = None

    if st.session_state["selected_job_id"]:
        render_job_detail(db, st.session_state["selected_job_id"])
    
    elif menu == "Dashboard":
        render_dashboard(db)

    elif menu == "Análise de E-mail":
        from app.review.email_analysis_ui import render_email_analysis_ui
        render_email_analysis_ui(db)

    elif menu == "Gestão de Contratos":
        from app.contracts.ui import render_contracts_ui
        render_contracts_ui()

    elif menu == "Execução Manual":
        # ... (Execution Manual code preserved)
        st.header("⚙️ Controle do Pipeline")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Ingestão (E-mail)")
            date_range = st.date_input("Filtrar por data de recebimento:", value=[datetime.now().date()], help="Selecione um dia ou arraste para selecionar um período.")
            
            if st.button("📥 Buscar E-mails (Ingestão)"):
                # Handle single date or range
                start_date = None
                end_date = None
                
                if isinstance(date_range, list) or isinstance(date_range, tuple):
                    if len(date_range) == 1:
                        start_date = date_range[0]
                        end_date = date_range[0]
                    elif len(date_range) == 2:
                        start_date = date_range[0]
                        end_date = date_range[1]

                with st.spinner("Conectando ao IMAP e buscando anexos..."):
                    ingestor = IngestionService(db)
                    ingestor.process_new_emails(start_date=start_date, end_date=end_date)
                st.success("Ingestão concluída!")
        
        with c2:
            st.subheader("2. Processamento (Extrator)")
            if st.button("🚀 Rodar Pipeline (OCR -> Classify -> Extract)"):
                with st.spinner("Processando Jobs em fila..."):
                    orch = PipelineOrchestrator(db)
                    orch.run_pipeline()
                st.success("Ciclo de processamento finalizado!")

    elif menu == "Relatórios":
        st.header("📂 Exportação de Dados")
        st.write("Gere relatórios consolidados em Excel com base nos dados extraídos.")
        
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Data Início")
        end_date = c2.date_input("Data Fim")
        
        if st.button("Gerar Excel"):
            svc = OutputService(db)
            excel_data = svc.generate_excel_report() # Add date filtering logic if needed in service call
            
            st.download_button(
                label="📥 Baixar Excel (.xlsx)",
                data=excel_data,
                file_name=f"relatorio_nf_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    elif menu == "Auditoria":
        render_observability(db)

    elif menu == "Configurações":
        st.header("⚙️ Configurações do Sistema")
        
        tab1, tab2 = st.tabs(["Filtros e Regras", "Infraestrutura (Read-only)"])
        
        with tab1:
            from app.contracts.ui import render_global_settings_ui
            render_global_settings_ui()
            
        with tab2:
            st.subheader("Configurações do Arquivo .env")
            st.write("Estes parâmetros são configurados via ambiente e requerem reinicialização para alteração.")
            st.json(settings.model_dump())

finally:
    db.close()
