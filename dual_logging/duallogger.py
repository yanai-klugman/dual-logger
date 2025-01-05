import asyncio
import logging
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from queue import Queue as SyncQueue
from typing import Any

from dual_logging.config.log_config import LoggerConfig
from dual_logging.core.console_logger import ConsoleLogger
from dual_logging.core.file_logger import FileLogger


class DualLogger(Logger):
    def __init__(self, name: str, level: int = logging.NOTSET, cfg: LoggerConfig = None):
        super().__init__(name, level)
        self.cfg = cfg or LoggerConfig(name=name)
        self.console_logger = ConsoleLogger(self.cfg)
        self.file_logger = FileLogger(self.cfg)

        self._console_queue = SyncQueue(self.cfg.console_queue_size)
        self._file_queue = SyncQueue(self.cfg.file_queue_size)
        self._async_queue = Queue(self.cfg.file_queue_size)

        self.executor = ThreadPoolExecutor()

        self.loop = None
        self.flush_task = None

        self.dropped_console_logs = 0
        self.dropped_file_logs = 0

        self.addHandler(self.console_logger.handler)
        self.addHandler(self.file_logger.handler)

    def _auto_detect_log(self, level: str, message: str, **ctx: Any) -> None:
        loop = self._get_or_create_loop()
        if loop.is_running():
            asyncio.create_task(self._log_async(level, message, **ctx))
        elif self.executor._shutdown:
            self._log_sync(level, message, **ctx)
        else:
            try:
                self.executor.submit(self._log_sync, level, message, **ctx)
            except RuntimeError:
                self._log_sync(level, message, **ctx)

    def _get_or_create_loop(self):
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            self.flush_task = self.loop.create_task(self._flush_periodically())
        return self.loop

    def _log_sync(self, level: str, message: str, **ctx: Any) -> None:
        if not self._console_queue.full():
            self._console_queue.put_nowait((level, message, ctx))
        else:
            self.dropped_console_logs += 1

        if not self._file_queue.full():
            self._file_queue.put_nowait((level, message, ctx))
        else:
            self.dropped_file_logs += 1

    async def _log_async(self, level: str, message: str, **ctx: Any) -> None:
        await self._async_queue.put((level, message, ctx))

    async def _flush_periodically(self) -> None:
        delay = 1  # Initial delay of 1 second
        max_delay = 60  # Cap the delay at 60 seconds

        while True:
            try:
                await asyncio.sleep(delay)
                self.flush()
                delay = 1  # Reset delay on success
            except Exception as e:
                print(f"Flush error: {e}")
                delay = min(delay * 2, max_delay)  # Exponential backoff

    def flush(self) -> None:
        while not self._console_queue.empty():
            level, message, ctx = self._console_queue.get_nowait()
            self.console_logger._log_sync(level, message, **ctx)

        while not self._file_queue.empty():
            level, message, ctx = self._file_queue.get_nowait()
            self.file_logger._log_sync(level, message, **ctx)

    async def flush_async(self) -> None:
        while not self._async_queue.empty():
            level, message, ctx = await self._async_queue.get()
            await self.file_logger._log_async(level, message, **ctx)

    def handle(self, record: logging.LogRecord) -> None:
        """Handle a LogRecord, dispatching it to both loggers."""
        self._auto_detect_log(record.levelname.lower(), record.msg, **record.__dict__)
        self.callHandlers(record)

    def shutdown(self) -> None:
        self.flush()
        if not self.executor._shutdown:
            self.executor.shutdown(wait=True)
        if self.flush_task:
            self.flush_task.cancel()
        logging.shutdown()

    def configure(self, cfg: LoggerConfig) -> None:
        """Dynamically reconfigure logger."""
        self.cfg = cfg
        self.setLevel(cfg.console_level_num)
        self.console_logger = ConsoleLogger(cfg)
        self.file_logger = FileLogger(cfg)

    # Standard logging methods
    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._auto_detect_log("debug", msg, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._auto_detect_log("info", msg, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._auto_detect_log("warning", msg, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._auto_detect_log("error", msg, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        # Route through auto detect to ensure consistency
        self._auto_detect_log("critical", message, **kwargs)

    def exception(self, message: str, *args: Any, exc_info: bool = True, **kwargs: Any) -> None:
        kwargs["exc_info"] = exc_info
        # Use auto detect to ensure it follows the same path
        self._auto_detect_log("error", message, **kwargs)
