from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activity import ReplyActivity, ReplyQuickReplyActivityParams, ReplyAudioActivityParams
    from linebot.v3.messaging.exceptions import ApiException


@dataclass
class HandleTextMessageWorkflowParams:
    reply_token: str
    quote_token: str
    message: str


@workflow.defn(name="HandleTextMessage")
class HandleTextMessageWorkflow:
    @workflow.run
    async def run(self, input: HandleTextMessageWorkflowParams) -> bool:
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=5),
            non_retryable_error_types=[ApiException.__name__],
        )

        match input.message.strip().lower():
            case text if any([keyword in text for keyword in ["pingu"]]):
                await workflow.execute_activity(
                    ReplyActivity.reply_quick_reply,  # type: ignore
                    ReplyQuickReplyActivityParams(
                        reply_token=input.reply_token,
                        quote_token=input.quote_token,
                        message="想讓 Pingu 怎麼叫 ?",
                        quick_messages=["叫", "驚訝", "生氣"],
                    ),
                    start_to_close_timeout=timedelta(seconds=5),
                    retry_policy=retry_policy,
                )
                return True

            case text if any([keyword in text for keyword in ["叫", "noot", "noot noot"]]):
                await workflow.execute_activity(
                    ReplyActivity.reply_audio,  # type: ignore
                    ReplyAudioActivityParams(
                        reply_token=input.reply_token,
                        content_url="https://static.weii.dev/audio/pingu/noot_noot.mp3",
                        duration=1000,
                    ),
                    start_to_close_timeout=timedelta(seconds=5),
                    retry_policy=retry_policy,
                )
                return True

            case text if any([keyword in text for keyword in ["驚訝", "驚"]]):
                await workflow.execute_activity(
                    ReplyActivity.reply_audio,  # type: ignore
                    ReplyAudioActivityParams(
                        reply_token=input.reply_token,
                        content_url="https://static.weii.dev/audio/pingu/amazed.mp3",
                        duration=1000,
                    ),
                    start_to_close_timeout=timedelta(seconds=5),
                    retry_policy=retry_policy,
                )
                return True

            case text if any([keyword in text for keyword in ["生氣", "氣"]]):
                await workflow.execute_activity(
                    ReplyActivity.reply_audio,  # type: ignore
                    ReplyAudioActivityParams(
                        reply_token=input.reply_token,
                        content_url="https://static.weii.dev/audio/pingu/sms.mp3",
                        duration=3000,
                    ),
                    start_to_close_timeout=timedelta(seconds=5),
                    retry_policy=retry_policy,
                )
                return True

            case _:
                return False
