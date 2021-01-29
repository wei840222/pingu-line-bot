import os
from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# get channel_secret and channel_access_token from your environment variable
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', None))

app = FastAPI()


@app.post("/callback")
async def callback(request: Request, response: Response):
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()

    # handle webhook body
    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return 'InvalidSignatureError'

    return 'OK'


app.mount("/static", StaticFiles(directory="static"), name="static")


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    if event.message.text == '叫':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0",
                port=8000, reload=True, debug=True)
