import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class QueueOverflowPolicy(Enum):
    DROP = "drop"
    BLOCK = "block"


@dataclass
class LoggerConfig:
    name: str = "dual_logger"
    singleton: bool = False
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    log_file_path: str | None = None
    rotate: bool = False
    max_bytes: int = 1_000_000
    backup_count: int = 3
    console_queue_size: int = 100
    file_queue_size: int = 100
    use_utc: bool = False
    time_format: str = "iso"
    queue_overflow_policy: QueueOverflowPolicy = QueueOverflowPolicy.DROP
    extra_ignores: list[str] = field(default_factory=lambda: ["asyncio", "socket"])

    def __post_init__(self) -> None:
        """Initialize logger configuration."""
        self.console_level_num = getattr(logging, self.console_level.upper(), logging.INFO)
        self.file_level_num = getattr(logging, self.file_level.upper(), logging.DEBUG)
        self.file_level_num = min(self.file_level_num, self.console_level_num)

        if not self.log_file_path:
            os.makedirs("logs", exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file_path = os.path.join("logs", f"app_{stamp}.log")
