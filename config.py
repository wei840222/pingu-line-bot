import sys
import logging
import structlog
from pydantic import Field
from typing import Optional
from structlog.types import EventDict, Processor
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: str = "info"
    format: str = "console"
    color: bool = True


class LoggerMixin:
    _logger: Optional[logging.Logger] = None

    # https://github.com/hynek/structlog/issues/35#issuecomment-591321744
    def _rename_event_key(_, __, event_dict: EventDict) -> EventDict:
        """
        Log entries keep the text message in the `event` field, but Datadog
        uses the `message` field. This processor moves the value from one field to
        the other.
        See https://github.com/hynek/structlog/issues/35#issuecomment-591321744
        """
        event_dict["message"] = event_dict.pop("event")
        return event_dict

    def _drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
        """
        Uvicorn logs the message a second time in the extra `color_message`, but we don't
        need it. This processor drops the key from the event dict if it exists.
        """
        event_dict.pop("color_message", None)
        return event_dict

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            config = LoggerConfig()

            timestamper = structlog.processors.TimeStamper(fmt="iso")

            shared_processors: list[Processor] = [
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.stdlib.ExtraAdder(),
                LoggerMixin._drop_color_message_key,
                timestamper,
                structlog.processors.StackInfoRenderer(),
            ]

            if config.format == "json":
                # We rename the `event` key to `message` only in JSON logs, as Datadog looks for the
                # `message` key but the pretty ConsoleRenderer looks for `event`
                shared_processors.append(LoggerMixin._rename_event_key)
                # Format the exception only for JSON logs, as we want to pretty-print them when
                # using the ConsoleRenderer
                shared_processors.append(structlog.processors.format_exc_info)

            structlog.configure(
                processors=shared_processors
                + [
                    # Prepare event dict for `ProcessorFormatter`.
                    structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
                ],
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )

            log_renderer: structlog.types.Processor
            if config.format == "json":
                log_renderer = structlog.processors.JSONRenderer()
            else:
                log_renderer = structlog.dev.ConsoleRenderer(
                    colors=config.color)

            formatter = structlog.stdlib.ProcessorFormatter(
                # These run ONLY on `logging` entries that do NOT originate within
                # structlog.
                foreign_pre_chain=shared_processors,
                # These run on ALL entries after the pre_chain is done.
                processors=[
                    # Remove _record & _from_structlog.
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    log_renderer,
                ],
            )

            handler = logging.StreamHandler()
            # Use OUR `ProcessorFormatter` to format all `logging` entries.
            handler.setFormatter(formatter)

            self._logger = logging.getLogger()
            self._logger.addHandler(handler)
            self._logger.setLevel(config.level.upper())

            for _log in ["uvicorn", "uvicorn.error"]:
                # Clear the log handlers for uvicorn loggers, and enable propagation
                # so the messages are caught by our root logger and formatted correctly
                # by structlog
                logging.getLogger(_log).handlers.clear()
                logging.getLogger(_log).propagate = True

            # Since we re-create the access logs ourselves, to add all information
            # in the structured log (see the `logging_middleware` in main.py), we clear
            # the handlers and prevent the logs to propagate to a logger higher up in the
            # hierarchy (effectively rendering them silent).
            logging.getLogger("uvicorn.access").handlers.clear()
            logging.getLogger("uvicorn.access").propagate = False

            def handle_exception(exc_type, exc_value, exc_traceback):
                """
                Log any uncaught exception instead of letting it be printed by Python
                (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
                See https://stackoverflow.com/a/16993115/3641865
                """
                if issubclass(exc_type, KeyboardInterrupt):
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return

                self._logger.error("Uncaught exception", exc_info=(  # pyright: ignore[reportOptionalMemberAccess]
                    exc_type, exc_value, exc_traceback))

            sys.excepthook = handle_exception

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
        default="default",
        description="The namespace for the Temporal workflows.")

    temporal_task_queue: str = Field(
        default="PINGU_BOT",
        description="The task queue for the Temporal worker.")


config = Config()  # type: ignore
logger = config.logger
