import sys
from loguru import logger
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

from config import settings

# Remove default handler
logger.remove()

# Add console handler
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Add file handler
log_dir = Path(settings.log_file).parent
log_dir.mkdir(parents=True, exist_ok=True)
logger.add(
    settings.log_file,
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="10 MB",
    retention="1 week"
)

class QueryLogger:
    """Structured logger for query operations"""

    def __init__(self):
        self.log_dir = log_dir / "queries"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_query(self, query_data: Dict[str, Any]):
        """Log a complete query with all outputs"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        log_file = self.log_dir / f"query_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(query_data, f, indent=2, default=str)

        logger.info(f"Query logged to {log_file}")

    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log an error with context"""
        error_data = {
            "error": str(error),
            "type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        logger.error(f"Error occurred: {error_data}")

    def log_performance(self, operation: str, latency_ms: float, cost: float = 0.0):
        """Log performance metrics"""
        logger.info(f"Performance: {operation} | Latency: {latency_ms:.2f}ms | Cost: ${cost:.6f}")

query_logger = QueryLogger()
