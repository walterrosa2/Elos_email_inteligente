import streamlit as st
from sqlalchemy.orm import Session
from app.db.models import EmailContext, Job

STATUS_COLORS = {
    "CRITICA": "red",
    "ALTA": "orange",
    "MEDIA": "blue",
    "BAIXA": "green"
}

def render_email_analysis_ui(db: Session):
    st.title("📧 Análise de Criticidade de E-mails")
    st.info("Monitoramento de tom e urgência das comunicações recebidas.")
    
    # metrics
    total = db.query(EmailContext).count()
    critical = db.query(EmailContext).filter(EmailContext.criticality_score.in_(["ALTA", "CRITICA"])).count()
    action = db.query(EmailContext).filter(EmailContext.action_required).count()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total E-mails", total)
    m2.metric("Alta Criticidade", critical, delta_color="inverse")
    m3.metric("Ação Necessária", action, delta_color="inverse")
    
    st.divider()
    
    # Filters
    st.caption("Filtros")
    from datetime import datetime, timedelta
    
    col_d1, col_d2 = st.columns(2)
    start_date = col_d1.date_input("De (Data Recebimento)", value=datetime.now() - timedelta(days=30))
    end_date = col_d2.date_input("Até", value=datetime.now())
    
    f1, f2 = st.columns(2)
    filter_crit = f1.multiselect("Filtrar Criticidade", ["BAIXA", "MEDIA", "ALTA", "CRITICA"], default=["ALTA", "CRITICA"])
    search_term = f2.text_input("Buscar (Assunto/Remetente)")
    
    # Query
    query = db.query(EmailContext)
    
    # Date Filter
    if start_date:
        query = query.filter(EmailContext.received_at >= start_date)
    if end_date:
         query = query.filter(EmailContext.received_at < (end_date + timedelta(days=1)))

    if filter_crit:
        query = query.filter(EmailContext.criticality_score.in_(filter_crit))
    if search_term:
        query = query.filter(
            (EmailContext.subject.ilike(f"%{search_term}%")) | 
            (EmailContext.sender.ilike(f"%{search_term}%"))
        )
        
    # Sort by criticality (custom sort hard in SQL, usually let's sort by date desc for now, or hacky case statement)
    # Simple: sort by received_at desc
    emails = query.order_by(EmailContext.received_at.desc()).limit(50).all()
    
    if not emails:
        st.warning("Nenhum e-mail encontrado com os filtros atuais.")
        return

    for email in emails:
        STATUS_COLORS.get(email.criticality_score, "grey")
        
        # Card
        with st.expander(f"[{email.criticality_score}] {email.subject} | {email.sender}"):
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.markdown(f"**Resumo IA:** {email.summary}")
                st.markdown(f"**Tom:** {email.tone}")
                
                if email.action_required:
                    st.error("⚠️ IA Sugere Ação Imediata")
                
                st.markdown("---")
                st.caption("Corpo do E-mail:")
                st.text_area("Body", email.body_text, height=150, disabled=True, key=f"body_{email.message_id}")

            with c2:
                st.write("**Anexos (Jobs):**")
                jobs = db.query(Job).filter(Job.message_id == email.message_id).all()
                if jobs:
                    for j in jobs:
                        st.write(f"📄 {j.attachment_name} ({j.status})")
                        # Could add button to jump to job details
                else:
                    st.write("Sem anexos.")
                
                st.caption(f"Recebido em: {email.received_at}")
