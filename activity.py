from dataclasses import dataclass
from temporalio import activity

from linebot.v3.messaging import (
    AsyncMessagingApi,
    ReplyMessageRequest,
    AudioMessage,
)

from config import logger


@dataclass
class ReplyAudioActivityParams:
    reply_token: str
    content_url: str
    duration: int


class ReplyActivity:
    def __init__(self, async_messaging_api: AsyncMessagingApi):
        self.line_bot_api = async_messaging_api

    @activity.defn(name="ReplyAudioActivity")
    async def reply_audio(self, input: ReplyAudioActivityParams) -> dict:
        response = await self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=input.reply_token,  # type: ignore
                messages=[AudioMessage(
                    original_content_url=input.content_url, duration=input.duration)]  # type: ignore
            )
        )
        logger.info("Reply audio message sent successfully.",
                    extra={"response": response})
        return response.to_dict()
