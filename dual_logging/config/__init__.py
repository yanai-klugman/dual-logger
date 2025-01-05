from .log_config import LoggerConfig, QueueOverflowPolicy
from .log_context import LogContextManager, logcontext

DROP_OVERFLOW = QueueOverflowPolicy.DROP
BLOCK_OVERFLOW = QueueOverflowPolicy.BLOCK

__all__ = [
    "LoggerConfig",
    "DROP_OVERFLOW",
    "BLOCK_OVERFLOW",
    "LogContextManager",
    "logcontext",
]
