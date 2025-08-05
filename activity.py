from dataclasses import dataclass
from temporalio import activity
from typing import Any, Dict, Optional
from typing_extensions import Annotated, Doc
from fastapi import HTTPException, status


from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    AudioMessage,
)

from linebot.v3.messaging.exceptions import ApiException

from config import Config

config = Config()
logger = config.get_logger()


@dataclass
class BadRequestHTTPException(HTTPException):
    """Exception for handling bad requests.
    This exception is raised when the request is invalid or malformed.
    """

    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc(
                """
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """
            ),
        ] = None,
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                """
                Any headers to send to the client in the response.
                """
            ),
        ] = None,
    ) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)


@dataclass
class ReplyAudioActivityParams:
    reply_token: str
    content_url: str
    duration: int


@activity.defn(name="ReplyAudioActivity")
async def reply_audio_activity(input: ReplyAudioActivityParams) -> Optional[Dict]:
    async_api_client = AsyncApiClient(Configuration(
        access_token=config.channel_access_token))
    line_bot_api = AsyncMessagingApi(async_api_client)
    try:
        response = await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=input.reply_token,  # type: ignore
                messages=[AudioMessage(
                    original_content_url=input.content_url, duration=input.duration)]  # type: ignore
            )  # type: ignore
        )
        logger.info(
            "Reply audio message sent successfully.", response=response.to_json())  # type: ignore
        return response.to_dict()
    except ApiException as e:
        if e.status == status.HTTP_400_BAD_REQUEST:
            raise BadRequestHTTPException(detail=e.body, headers=e.headers)
        raise e
    finally:
        await async_api_client.close()
        logger.debug("AsyncApiClient closed.")
