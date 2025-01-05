import logging
from typing import Any
from unittest.mock import patch

import pytest

from dual_logging.config.log_config import LoggerConfig
from dual_logging.duallogger import DualLogger


@pytest.fixture
def logger_config():
    return LoggerConfig(
        name="test_logger",
        console_level="DEBUG",
        file_level="DEBUG",
        log_file_path="logs/test_log.log",
        console_queue_size=3,
        file_queue_size=3,
    )


@pytest.fixture
def dual_logger(logger_config):
    logging.setLoggerClass(DualLogger)
    logger = logging.getLogger(logger_config.name)
    logger.configure(logger_config)
    yield logger
    logger.shutdown()  # This will stop the executor, no logging afterward.


EXPECTED_CALL_COUNT: int = 5


def test_sync_logging_methods(dual_logger):
    with patch.object(dual_logger, "_auto_detect_log") as mock_auto_detect:
        dual_logger.debug("Debug message", trace_id="123")
        dual_logger.info("Info message", trace_id="456")
        dual_logger.warning("Warning message", trace_id="789")
        dual_logger.error("Error message", trace_id="012")
        dual_logger.critical("Critical message", trace_id="345")

        assert mock_auto_detect.call_count == EXPECTED_CALL_COUNT


@pytest.mark.asyncio
async def test_async_logging_methods(dual_logger):
    with patch.object(dual_logger, "_log_async") as mock_log_async:
        await dual_logger._log_async("info", "Async info message")
        await dual_logger._log_async("debug", "Async debug message")
        await dual_logger._log_async("warning", "Async warning message")
        await dual_logger._log_async("error", "Async error message")
        await dual_logger._log_async("critical", "Async critical message")

        assert mock_log_async.call_count == EXPECTED_CALL_COUNT


def test_exception_logging(dual_logger):
    with patch.object(dual_logger, "_log_sync") as mock_log_sync:
        try:
            raise ValueError("Test exception")
        except ValueError:
            dual_logger.exception("Exception occurred")

        mock_log_sync.assert_called_once_with("error", "Exception occurred", exc_info=True)


def _log_sync(self, level: str, message: str, **ctx: Any) -> None:
    if not self._console_queue.full():
        self._console_queue.put_nowait((level, message, ctx))
    else:
        self.dropped_console_logs += 1

    if not self._file_queue.full():
        self._file_queue.put_nowait((level, message, ctx))
    else:
        self.dropped_file_logs += 1


@pytest.mark.asyncio
async def test_async_flush(dual_logger):
    with patch.object(dual_logger.file_logger, "_log_async"):
        for _ in range(3):
            dual_logger.debug("Async flush test message")
        await dual_logger.flush_async()
