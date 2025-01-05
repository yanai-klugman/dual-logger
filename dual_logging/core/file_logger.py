import logging
from logging.handlers import RotatingFileHandler
from typing import Any

import aiofiles
import structlog
from structlog.processors import (
    CallsiteParameter,
    CallsiteParameterAdder,
    JSONRenderer,
    TimeStamper,
    add_log_level,
)

from ..config.log_config import LoggerConfig
from .base_logger import BaseLogger


class FileLogger(BaseLogger):
    def __init__(self, cfg: LoggerConfig) -> None:
        self.cfg = cfg
        self._logger = logging.Logger(f"{cfg.name}-file")
        self._logger.setLevel(cfg.file_level_num)

        if not self._logger.handlers:
            self.handler = RotatingFileHandler(
                cfg.log_file_path,
                maxBytes=cfg.max_bytes,
                backupCount=cfg.backup_count,
            )
            self.handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(self.handler)
        else:
            self.handler = self._logger.handlers[0]

        pipeline = [
            TimeStamper(fmt=cfg.time_format, utc=cfg.use_utc),
            add_log_level,
            CallsiteParameterAdder(
                parameters=[CallsiteParameter.PATHNAME, CallsiteParameter.LINENO],
                additional_ignores=cfg.extra_ignores,
            ),
            JSONRenderer(),
        ]
        self._struct_logger = structlog.wrap_logger(self._logger, processors=pipeline)

    def _log_sync(self, level: str, message: str, exc_info: bool = False, **ctx: Any) -> None:
        logger = self._struct_logger.bind(**ctx)
        getattr(logger, level)(message, exc_info=exc_info)
        logger.unbind(*ctx.keys())

    async def _log_async(
        self, level: str, message: str, exc_info: bool = False, **ctx: Any
    ) -> None:
        log_entry = structlog.processors.JSONRenderer()({
            "level": level.upper(),
            "event": message,
            "exc_info": exc_info,
            "timestamp": TimeStamper(fmt=self.cfg.time_format, utc=self.cfg.use_utc)(),
            **ctx,
        })
        await self._write_log(log_entry)

    async def _write_log(self, log_entry: str) -> None:
        async with aiofiles.open(self.cfg.log_file_path, "a") as f:
            await f.write(log_entry + "\n")

    def flush(self) -> None:
        self.handler.flush()
        for handler in self._logger.handlers:
            handler.flush()
