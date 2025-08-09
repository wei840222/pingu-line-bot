import logging
import structlog
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: str = "INFO"


class LoggerMixin:
    _logger: Optional[logging.Logger] = None

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            config = LoggerConfig()
            structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, config.level.upper())))
            self._logger = structlog.stdlib.get_logger()  # type: ignore
        return self._logger  # type: ignore


class Config(BaseSettings, LoggerMixin):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    line_channel_secret: str = Field(
        description="The secret key for the LINE channel.")

    line_channel_access_token: str = Field(
        description="The access token for the LINE  channel.")

    temporal_address: str = Field(
        default="localhost:7233",
        description="The address of the Temporal frontend server.")

    temporal_namespace: str = Field(
        default="bot-farm",
        description="The namespace for the Temporal workflows.")

    temporal_task_queue: str = Field(
        default="PINGU_BOT",
        description="The task queue for the Temporal worker.")


config = Config()  # type: ignore
logger = config.logger
