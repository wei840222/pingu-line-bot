from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow
from temporalio.common import RetryPolicy
from linebot.v3.messaging.exceptions import ApiException

with workflow.unsafe.imports_passed_through():
    from activity import ReplyActivity, ReplyAudioActivityParams


@dataclass
class HandleTextMessageWorkflowParams:
    reply_token: str
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

        if input.message == "叫":
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

        return False
