from app.db.database import engine, Base
from app.core.logging import setup_logging, logger

def init_db():
    setup_logging()
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

if __name__ == "__main__":
    init_db()
