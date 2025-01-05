import asyncio

from dual_logging import BLOCK_OVERFLOW, DualLogger, LoggerConfig


async def main():
    # Step 1: Logger Configuration
    logger_config = LoggerConfig(
        name="demo_logger",
        console_level="INFO",
        file_level="DEBUG",
        log_file_path="/tmp/demo_logger_output.log",
        console_queue_size=5,
        queue_overflow_policy=BLOCK_OVERFLOW,
    )
    logger = DualLogger(logger_config)

    logger.info("=== Dual Logger Demo: Start ===")

    # Step 2: Logging Below Threshold
    logger.info("Logger initialized successfully.")
    logger.info("Logging messages below queue size threshold.")

    for i in range(4):
        await logger.ainfo(f"Message {i + 1}")
    logger.info("Messages logged without overflow.")

    # Step 3: Force Overflow
    logger.info("Forcing queue overflow by exceeding queue size.")

    for i in range(10):
        result = await logger.ainfo(f"Overflow test {i + 1}")
        if not result:
            logger.warning(f"Overflow occurred at message {i + 1}")
    logger.info("Overflow test completed.")

    # Step 4: Flush Logs
    logger.info("Flushing remaining logs.")
    logger.flush()
    logger.info("Logs flushed to file.")

    # Step 5: Display Stats
    logger.info(f"Final dropped logs: {logger.dropped_console_logs}")
    logger.info(f"Queue size after flush: {logger.get_queue_size()}")

    # Step 6: Simulate Error Logging
    logger.info("Logging an error with traceback.")
    try:
        raise ValueError("Simulated exception for error logging")
    except Exception:
        logger.exception("Caught an exception during execution")

    # Step 7: Test Different Log Levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Step 8: Async Error Logging
    logger.info("Testing asynchronous exception logging.")
    try:
        await async_error_log(logger)
    except Exception as e:
        logger.exception(f"Unhandled async error: {str(e)}")

    logger.flush()
    logger.info("Demo complete. Check the log file for full output.")
    logger.info("=== Dual Logger Demo: End ===")


async def async_error_log(logger):
    raise RuntimeError("Async error for demonstration")


# Synchronous entry point
def sync_entry():
    asyncio.run(main())


if __name__ == "__main__":
    sync_entry()
