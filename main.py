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

# Get channel_secret and channel_access_token from your environment variable
if config.channel_secret is None:
    raise ValueError("Specify LINE_CHANNEL_SECRET as environment variable.")
if config.channel_access_token is None:
    raise ValueError(
        "Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")

app = FastAPI()


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers["X-Line-Signature"]

    # Get request body as text
    body = await request.body()
    body = body.decode()
    parser = WebhookParser(config.channel_secret)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Create the LINE Bot API client inside the async function
    configuration = Configuration(access_token=config.channel_access_token)
    async_api_client = AsyncApiClient(configuration)
    line_bot_api = AsyncMessagingApi(async_api_client)

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
