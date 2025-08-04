from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from logger import LoggerMixin


class Config(BaseSettings, LoggerMixin):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    channel_secret: Optional[str] = Field(
        default=None,
        description="The secret key for the channel.")

    channel_access_token: Optional[str] = Field(
        default=None,
        description="The access token for the channel.")
