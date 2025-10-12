from typing import List
from dataclasses import dataclass
from temporalio import activity

from linebot.v3.messaging import (
    AsyncMessagingApi,
    ReplyMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    AudioMessage,
)

from config import logger


@dataclass
class ReplyTokenParams:
    reply_token: str


@dataclass
class ReplyQuickReplyActivityParams(ReplyTokenParams):
    quote_token: str
    message: str
    quick_messages: List[str]


@dataclass
class ReplyAudioActivityParams(ReplyTokenParams):
    content_url: str
    duration: int


class ReplyActivity:
    def __init__(self, async_messaging_api: AsyncMessagingApi):
        self.line_bot_api = async_messaging_api

    @activity.defn(name="ReplyQuickReplyActivity")
    async def reply_quick_reply(self, input: ReplyQuickReplyActivityParams) -> dict:
        response = await self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=input.reply_token,  # type: ignore
                messages=[
                    TextMessage(
                        quote_token=input.quote_token,  # type: ignore
                        text=input.message,
                        quick_reply=QuickReply(  # type: ignore
                            items=[
                                QuickReplyItem(
                                    action=MessageAction(label=text, text=text)
                                )
                                for text in input.quick_messages  # type: ignore
                            ]
                        ),
                    )
                ],  # type: ignore
            )
        )
        logger.info(
            "Reply audio message sent successfully.", extra={"response": response}
        )
        return response.to_dict()

    @activity.defn(name="ReplyAudioActivity")
    async def reply_audio(self, input: ReplyAudioActivityParams) -> dict:
        response = await self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=input.reply_token,  # type: ignore
                messages=[
                    AudioMessage(
                        original_content_url=input.content_url, duration=input.duration
                    )
                ],  # type: ignore
            )
        )
        logger.info(
            "Reply audio message sent successfully.", extra={"response": response}
        )
        return response.to_dict()
