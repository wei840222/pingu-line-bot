import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, AudioSendMessage

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None))
bot = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', None))
base_url = os.getenv('BASE_URL', None)


@app.post('/callback')
async def callback(request: Request):
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    bot.handle(body.decode('utf-8'), signature)
    return 'OK'


@bot.add(MessageEvent, message=TextMessage)
def message_text(event):
    if event.message.text == '叫':
        line_bot_api.reply_message(
            event.reply_token, AudioSendMessage(original_content_url=base_url + '/static/audio/noot_noot.mp3', duration=1000))


if __name__ == '__main__':
    uvicorn.run('server:app', reload=True, debug=True)
