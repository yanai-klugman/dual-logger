import contextvars
import inspect
from collections.abc import Callable, Generator
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import Any


class LogContextManager:
    def __init__(self):
        self.log_context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
            "log_context", default=None
        )

    def _get_log_context(self) -> dict[str, Any]:
        """Retrieve the current log context, initializing if necessary."""
        current_context = self.log_context.get(None)
        if current_context is None:
            current_context = {}
            self.log_context.set(current_context)
        return current_context

    def _set_log_context(self, new_ctx: dict[str, Any]) -> None:
        """Set or update the log context."""
        self.log_context.set(new_ctx)

    @contextmanager
    def context(self, temp_ctx: dict[str, Any]) -> Generator[None, None, None]:
        """Temporarily modify the log context."""
        current_context = self._get_log_context().copy()
        try:
            current_context.update(temp_ctx)
            self._set_log_context(current_context)
            yield
        finally:
            self._set_log_context(current_context)

    @asynccontextmanager
    async def async_context(self, temp_ctx: dict[str, Any]) -> Generator[None, None, None]:
        """Asynchronous context manager for modifying the log context."""
        current_context = self._get_log_context().copy()
        try:
            current_context.update(temp_ctx)
            self._set_log_context(current_context)
            yield
        finally:
            self._set_log_context(current_context)

    def decorator(self, temp_ctx: dict[str, Any]):
        """Apply temporary log context during function execution."""

        def decorator(func: Callable):
            @wraps(func)
            def sync_wrapper(*args: str, **kwargs: Any):
                with self.context(temp_ctx):
                    return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args: str, **kwargs: Any):
                async with self.async_context(temp_ctx):
                    return await func(*args, **kwargs)

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


# Singleton instance for easy access
_log_context_manager = LogContextManager()
logcontext = _log_context_manager.decorator
