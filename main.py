import asyncio
from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, Request, HTTPException, status
from temporalio.client import Client as TemporalClient
from temporalio.worker import Worker as TemporalWorker

from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
)

from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from config import config, logger
from workflow import HandleTextMessageWorkflow, HandleTextMessageWorkflowParams
from activity import ReplyActivity


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await TemporalClient.connect(config.temporal_address, namespace=config.temporal_namespace)
    app.state.temporal_client = client
    logger.debug("Connected to Temporal server.", extra={
                 "address": config.temporal_address, "namespace": config.temporal_namespace})

    line_bot_api = AsyncMessagingApi(AsyncApiClient(Configuration(
        access_token=config.line_channel_access_token)))

    reply_activity = ReplyActivity(line_bot_api)

    worker = TemporalWorker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[HandleTextMessageWorkflow],
        activities=[reply_activity.reply_audio],
    )

    task = asyncio.create_task(worker.run())
    logger.info("Temporal worker started.", extra={
                "task_queue": config.temporal_task_queue})

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        await worker.shutdown()
        logger.info(
            "Application shutdown: Temporal worker shutdown gracefully.")
        await line_bot_api.api_client.close()
        config.logger.debug("Application shutdown: LINE API Client closed.")

app = FastAPI(lifespan=lifespan, docs_url=None,
              redoc_url=None, openapi_url=None)


@app.post("/callback", status_code=status.HTTP_202_ACCEPTED)
async def handle_callback(request: Request, x_line_signature: Annotated[str, Header()]):
    body = await request.body()

    try:
        events = WebhookParser(config.line_channel_secret).parse(
            body.decode(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature.")

    temporal_client: TemporalClient = app.state.temporal_client

    for event in events:  # type: ignore
        logger.debug("Received webhook event.", extra={"event": event})
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue

        handle = await temporal_client.start_workflow(
            HandleTextMessageWorkflow.run,
            HandleTextMessageWorkflowParams(
                reply_token=event.reply_token,  # type: ignore
                message=event.message.text
            ),
            id=event.webhook_event_id,
            task_queue=config.temporal_task_queue,
        )
        logger.info("Started workflow for handling text message.", extra={
                    "task_queue": config.temporal_task_queue, "workflow_id": handle.id, "run_id": handle.run_id})

    return "ACCEPTED"
