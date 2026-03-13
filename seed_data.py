from app.db.database import SessionLocal, engine, Base
from app.db.models import Job, EmailContext
from datetime import datetime, timedelta

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    try:
        print("🌱 Seeding database with test jobs AND email contexts...")
        
        # 1. Contexto Crítico
        msg_crit = "msg_crit_001"
        ctx_crit = EmailContext(
            message_id=msg_crit,
            subject="URGENTE: Cancelamento de Contrato - Fatura em Atraso",
            sender="cliente.irritado@empresa.com",
            received_at=datetime.now(),
            body_text="Prezados, esta é a terceira tentativa de contato. Se o boleto anexo não for pago até hoje, cancelaremos o serviço amanhã sem falta. Aguardo retorno IMEDIATO.",
            criticality_score="CRITICA",
            tone="Agressivo",
            summary="Ameaça de cancelamento por falta de pagamento.",
            action_required=True,
            raw_analysis_json={"criticidade": 5, "tom": "Agressivo"}
        )
        db.add(ctx_crit)

        job_crit = Job(
            job_hash="hash_crit_1",
            message_id=msg_crit,
            sender="cliente.irritado@empresa.com",
            subject="URGENTE: Cancelamento de Contrato",
            email_date=datetime.now(),
            received_at=datetime.now(),
            attachment_name="boleto_atrasado.pdf",
            storage_uri="C:\\fake\\boleto.pdf",
            status="REVIEW_PENDING",
            doc_type="boleto_bancario"
        )
        db.add(job_crit)

        # 2. Contexto Normal
        msg_norm = "msg_norm_002"
        ctx_norm = EmailContext(
            message_id=msg_norm,
            subject="Envio de Nota Fiscal - Prestação de Serviço",
            sender="fornecedor@servicos.com",
            received_at=datetime.now() - timedelta(hours=2),
            body_text="Olá, segue em anexo a nota fiscal referente aos serviços de limpeza deste mês. Obrigado.",
            criticality_score="BAIXA",
            tone="Formal",
            summary="Envio de NF de serviços de rotina.",
            action_required=False
        )
        db.add(ctx_norm)
        
        job_norm = Job(
            job_hash="hash_norm_1",
            message_id=msg_norm,
            sender="fornecedor@servicos.com",
            subject="Envio de Nota Fiscal",
            email_date=datetime.now(),
            received_at=datetime.now(),
            attachment_name="nfe_servico.pdf",
            storage_uri="C:\\fake\\nfe.pdf",
            status="APPROVED",
            doc_type="nfse_nacional"
        )
        db.add(job_norm)

        db.commit()
        print("✅ Added Test Data: 1 Critical Email, 1 Normal Email.")
        print("🚀 Refresh the 'Análise de E-mail' page to see the results.")
        
    except Exception as e:
        print(f"❌ Error seeding DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
