import os
import uvicorn
import fastapi
import linebot
import fastapi.staticfiles as fastapiStaticfiles
import linebot.models as linebotModels

app = fastapi.FastAPI()
app.mount(
    "/static", fastapiStaticfiles.StaticFiles(directory="static"), name="static")

lineBotApi = linebot.LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None))
bot = linebot.WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', None))
base_url = os.getenv('BASE_URL', None)


@app.post('/callback')
async def callback(request: fastapi.Request):
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    bot.handle(body.decode('utf-8'), signature)
    return 'OK'


@bot.add(linebotModels.MessageEvent, message=linebotModels.TextMessage)
def message_text(event):
    if event.message.text == '叫':
        lineBotApi.reply_message(
            event.reply_token, linebotModels.AudioSendMessage(
                original_content_url=base_url + '/static/audio/noot_noot.mp3', duration=1000))


if __name__ == '__main__':
    uvicorn.run('server:app', reload=True, debug=True)
