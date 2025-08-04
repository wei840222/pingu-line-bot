import logging
from typing import Optional

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger: Optional[logging.Logger] = None


class LoggerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: str = "INFO"

    @property
    def logger(self) -> logging.Logger:
        global _logger
        if _logger is None:
            structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, self.level.upper())))
            _logger = structlog.stdlib.get_logger()  # type: ignore
        return _logger  # type: ignore


class LoggerMixin:
    _logger_config: Optional[LoggerConfig] = None

    def get_logger(self) -> logging.Logger:
        if self._logger_config is None:
            self._logger_config = LoggerConfig()
        return self._logger_config.logger
