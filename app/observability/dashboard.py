import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Job

def render_observability(db: Session):
    st.title("📈 Observabilidade e Auditoria")

    # 1. Job Status Distribution
    st.subheader("Distribuição por Status")
    status_counts = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    if status_counts:
        df_status = pd.DataFrame(status_counts, columns=["Status", "Count"])
        fig_status = px.pie(df_status, values="Count", names="Status", title="Jobs por Status")
        st.plotly_chart(fig_status)
    else:
        st.info("Sem dados para exibir.")

    # 2. Document Types
    st.subheader("Tipos de Documentos Detectados")
    type_counts = db.query(Job.doc_type, func.count(Job.id)).filter(Job.doc_type.isnot(None)).group_by(Job.doc_type).all()
    if type_counts:
        df_types = pd.DataFrame(type_counts, columns=["Tipo", "Count"])
        fig_types = px.bar(df_types, x="Tipo", y="Count", title="Volume por Tipo de Documento")
        st.plotly_chart(fig_types)

    # 3. Timeline (Jobs per Day)
    st.subheader("Volume Diário")
    # SQLite doesn't suport complex date func easily in pure SQL for grouping day without cast
    # fetching raw for pandas processing (assuming volume isn't massive for MVP)
    jobs = db.query(Job.created_at).all()
    if jobs:
        dates = [j.created_at.date() for j in jobs]
        df_timeline = pd.DataFrame({"Data": dates, "Count": 1})
        df_timeline = df_timeline.groupby("Data").sum().reset_index()
        fig_timeline = px.line(df_timeline, x="Data", y="Count", title="Jobs Processados por Dia")
        st.plotly_chart(fig_timeline)

