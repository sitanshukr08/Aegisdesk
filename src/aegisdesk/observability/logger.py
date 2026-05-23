import logging
import logging.handlers
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Standard log format for enterprise monitoring (Splunk/Datadog friendly)
LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"

def get_logger(name: str) -> logging.Logger:
    """
    Returns a centralized logger configured for both console and file output.
    Implements RotatingFileHandler to prevent server disk overflow.
    """
    logger = logging.getLogger(name)
    
    # Only configure if the logger has no handlers (prevents duplicate logs)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # 1. Console Handler (Only shows INFO and above to keep terminal clean)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)

        # 2. Rotating File Handler (Keeps all DEBUG logs, rotates at 10MB, keeps last 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "aegisdesk.log", 
            maxBytes=10 * 1024 * 1024, # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
