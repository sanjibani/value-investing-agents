import sys
from loguru import logger

def setup_logger():
    """Configure logger"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG"
    )
    return logger
