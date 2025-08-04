from contextlib import asynccontextmanager
from fastapi import Request, FastAPI, HTTPException

from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from config import Config

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

    app.state.line_webhook_parser = WebhookParser(config.channel_secret)

    configuration = Configuration(access_token=config.channel_access_token)
    async_api_client = AsyncApiClient(configuration)
    app.state.line_bot_api = AsyncMessagingApi(async_api_client)

    yield

    await async_api_client.close()


app = FastAPI(lifespan=lifespan)


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers["X-LINE-Signature"]

    # Get request body as text
    body = await request.body()
    parser: WebhookParser = app.state.line_webhook_parser

    try:
        events = parser.parse(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    line_bot_api: AsyncMessagingApi = app.state.line_bot_api

    for event in events:  # type: ignore
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue

        await line_bot_api.reply_message(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=event.message.text)]  # type: ignore
            )  # type: ignore
        )

    return "OK"
