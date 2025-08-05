from dataclasses import dataclass
from temporalio import activity
from typing import Dict


from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    AudioMessage,
    ReplyMessageResponse,
)

from config import Config

config = Config()
logger = config.get_logger()


@dataclass
class ReplyAudioActivityParams:
    reply_token: str
    content_url: str
    duration: int


@activity.defn(name="ReplyAudioActivity")
async def reply_audio_activity(input: ReplyAudioActivityParams) -> Dict:
    async_api_client = AsyncApiClient(Configuration(
        access_token=config.channel_access_token))
    line_bot_api = AsyncMessagingApi(async_api_client)
    response = await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=input.reply_token,  # type: ignore
            messages=[AudioMessage(
                original_content_url=input.content_url, duration=input.duration)]  # type: ignore
        )  # type: ignore
    )
    logger.info(
        "Reply audio message sent successfully.", response=response.to_json())  # type: ignore
    await async_api_client.close()
    return response.to_dict()
