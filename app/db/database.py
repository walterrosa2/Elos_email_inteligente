from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Import all models and create tables if they don't exist yet."""
    from app.db import models  # noqa: F401 – registers all models with Base
    Base.metadata.create_all(bind=engine)
    
    # Executa migrações ad-hoc para colunas de roteamento se necessário
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "jobs" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("jobs")]
        new_cols = {
            "direction_status": "TEXT DEFAULT 'PENDING'",
            "routed_at": "DATETIME",
            "routed_path": "TEXT",
            "target_payment_date": "TEXT",
            "detected_due_date": "TEXT",
            "due_date_source": "TEXT",
            "due_date_context": "TEXT",
            "original_due_date": "TEXT",
            "email_body_due_date": "TEXT"
        }
        with engine.begin() as conn:
            for col_name, col_type in new_cols.items():
                if col_name not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}"))
                        # Criar índice para direction_status se necessário
                        if col_name == "direction_status":
                            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_jobs_direction_status ON jobs (direction_status)"))
                    except Exception as e:
                        # logger não está importado aqui, mas podemos apenas ignorar ou imprimir
                        print(f"Erro ao adicionar coluna {col_name} via ALTER TABLE na tabela jobs: {e}")
                        
    if "email_contexts" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("email_contexts")]
        new_cols = {
            "detected_due_date": "TEXT",
            "due_date_context": "TEXT"
        }
        with engine.begin() as conn:
            for col_name, col_type in new_cols.items():
                if col_name not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE email_contexts ADD COLUMN {col_name} {col_type}"))
                    except Exception as e:
                        print(f"Erro ao adicionar coluna {col_name} via ALTER TABLE na tabela email_contexts: {e}")
                        
    # Inicializar payment_routing_settings se nao existir
    if "system_settings" in inspector.get_table_names():
        with engine.begin() as conn:
            result = conn.execute(text("SELECT key FROM system_settings WHERE key = 'payment_routing_settings'")).first()
            if not result:
                import json
                from app.routing.service import DEFAULT_SETTINGS
                default_val_json = json.dumps(DEFAULT_SETTINGS)
                try:
                    conn.execute(
                        text("INSERT INTO system_settings (key, value, description) VALUES (:key, :value, :desc)"),
                        {"key": "payment_routing_settings", "value": default_val_json, "desc": "Configuracoes de Roteamento de Pagamentos (V3.0)"}
                    )
                except Exception as e:
                    print(f"Erro ao inicializar payment_routing_settings no banco: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
