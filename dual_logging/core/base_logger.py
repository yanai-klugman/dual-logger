from abc import ABC, abstractmethod
from typing import Any


class BaseLogger(ABC):
    @abstractmethod
    def _log_sync(self, level: str, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        pass

    @abstractmethod
    async def _log_async(
        self, level: str, message: str, exc_info: bool = False, **kwargs: Any
    ) -> None:
        pass

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log_sync("debug", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log_sync("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log_sync("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log_sync("error", message, **kwargs)

    def exception(self, message: str, exc_info: bool = True, **kwargs: Any) -> None:
        self._log_sync("error", message, exc_info=exc_info, **kwargs)

    async def adebug(self, message: str, **kwargs: Any) -> None:
        await self._log_async("debug", message, **kwargs)

    async def ainfo(self, message: str, **kwargs: Any) -> None:
        await self._log_async("info", message, **kwargs)

    async def awarning(self, message: str, **kwargs: Any) -> None:
        await self._log_async("warning", message, **kwargs)

    async def aerror(self, message: str, **kwargs: Any) -> None:
        await self._log_async("error", message, **kwargs)

    async def aexception(self, message: str, exc_info: bool = True, **kwargs: Any) -> None:
        await self._log_async("error", message, exc_info=exc_info, **kwargs)
