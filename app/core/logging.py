import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """Configures the logging system using Loguru."""
    logger.remove()  # Remove default handler

    # Console handler (Human readable)
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # File handler (JSON for observability tools)
    from pathlib import Path
    log_path = Path("logs/app.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_path,
        rotation="10 MB",
        retention="30 days",
        level=settings.LOG_LEVEL,
        serialize=True,
        enqueue=True,
    )

    logger.info("Logging system initialized.")
