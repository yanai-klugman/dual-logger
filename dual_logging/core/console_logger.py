import logging
from typing import Any

from rich.logging import RichHandler

from ..config.log_config import LoggerConfig
from .base_logger import BaseLogger


class ConsoleLogger(BaseLogger):
    def __init__(self, cfg: LoggerConfig) -> None:
        self._logger = logging.Logger(f"{cfg.name}-console")
        self._logger.setLevel(cfg.console_level_num)

        if not self._logger.handlers:
            self.handler = RichHandler(
                show_time=True,
                show_level=True,
                show_path=True,
                rich_tracebacks=True,
            )
            self._logger.addHandler(self.handler)
        else:
            self.handler = self._logger.handlers[0]

    def _log_sync(self, level: str, message: str, exc_info: bool = False, **ctx: Any) -> None:
        ctx.pop("trace_id", None)
        extra = " ".join(f"{k}={v}" for k, v in ctx.items())
        fn = getattr(self._logger, level.lower(), self._logger.info)
        fn(f"{message} {extra}", exc_info=exc_info)

    async def _log_async(
        self, level: str, message: str, exc_info: bool = False, **ctx: Any
    ) -> None:
        self._log_sync(level, message, exc_info, **ctx)
