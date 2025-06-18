from loguru import logger
import sys
from datetime import datetime

logger.remove()
logger.add(
    f"logs/{datetime.now().strftime('%Y-%m-%d')}.log",
    rotation="00:00",
    retention="10 days",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    level="INFO"
)
logger.add(sys.stderr, level="INFO")