import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import Request, FastAPI, HTTPException, status
from temporalio.client import Client as TemporalClient
from temporalio.worker import Worker as TemporalWorker

from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)


from config import Config
from workflow import HandleTextMessageWorkflow, HandleTextMessageWorkflowParams
from activity import reply_audio_activity

config = Config()
logger = config.get_logger()
logger.debug("Config loaded.", config=config)  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    if config.channel_secret is None:
        raise ValueError(
            "Specify LINE_CHANNEL_SECRET as environment variable.")
    if config.channel_access_token is None:
        raise ValueError(
            "Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")

    client = await TemporalClient.connect(config.temporal_address)
    app.state.temporal_client = client
    worker = TemporalWorker(
        client,
        task_queue="PINGU_BOT",
        workflows=[HandleTextMessageWorkflow],
        activities=[reply_audio_activity],
    )

    task = asyncio.create_task(worker.run())
    logger.info("Temporal worker started.")

    yield

    task.cancel()
    try:
        await task  # Wait for the task to finish canceling
    except asyncio.CancelledError:
        await worker.shutdown()
        logger.info(
            "Application shutdown: Temporal worker shutdown gracefully.")

app = FastAPI(lifespan=lifespan)


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers["X-LINE-Signature"]

    # Get request body as text
    body = await request.body()

    try:
        events = WebhookParser(config.channel_secret).parse(
            body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    temporal_client: TemporalClient = app.state.temporal_client

    for event in events:  # type: ignore
        logger.debug("Received webhook event.",
                     data=event.to_json())  # type: ignore
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue

        await temporal_client.start_workflow(
            HandleTextMessageWorkflow.run,
            HandleTextMessageWorkflowParams(
                reply_token=event.reply_token,  # type: ignore
                message=event.message.text
            ),
            id=str(uuid.uuid4()),
            task_queue="PINGU_BOT",
        )

    return "OK"
