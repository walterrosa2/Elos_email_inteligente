import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """Confingures the application logging using Loguru."""
    
    # Define log path based on settings (e.g., ./dados/logs/app.log)
    # Ideally logs are also separated by date in the folder structure logic, 
    # but a central log is good for the application runner.
    log_dir = settings.DATA_ROOT / "logs"
    log_file = log_dir / "app_{time:YYYY-MM-DD}.log"
    
    # Remove default handler to avoid duplicate logs if re-initialized
    logger.remove()
    
    # Add Console Handler
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add File Handler
    # Rotating daily not strictly necessary if filename includes date, but good practice.
    # We use retention from settings.
    logger.add(
        str(log_file),
        rotation="00:00", # New file at midnight
        retention=f"{settings.RETENCAO_DIAS} days",
        level="DEBUG",
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {extra} | {message}"
    )

    logger.info("Logging system initialized.")
