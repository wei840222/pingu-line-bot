package main

import (
	"embed"
	"fmt"
	"log"
	"net/http"
	"os"
	"path"
	"strings"

	"github.com/line/line-bot-sdk-go/v7/linebot"
	"github.com/line/line-bot-sdk-go/v7/linebot/httphandler"
)

//go:embed static
var staticFiles embed.FS

func joinURL(base string, paths ...string) string {
	p := path.Join(paths...)
	return fmt.Sprintf("%s/%s", strings.TrimRight(base, "/"), strings.TrimLeft(p, "/"))
}

func main() {
	baseURL := os.Getenv("BASE_URL")

	linebotHandler, err := httphandler.New(
		os.Getenv("LINE_CHANNEL_SECRET"),
		os.Getenv("LINE_CHANNEL_TOKEN"),
	)
	if err != nil {
		log.Fatal(err)
	}

	linebotHandler.HandleEvents(func(events []*linebot.Event, r *http.Request) {
		bot, err := linebotHandler.NewClient()
		if err != nil {
			log.Print(err)
			return
		}
		for _, event := range events {
			if event.Type == linebot.EventTypeMessage {
				switch message := event.Message.(type) {
				case *linebot.TextMessage:
					if message.Text == "叫" {
						if _, err = bot.ReplyMessage(event.ReplyToken, linebot.NewAudioMessage(joinURL(baseURL, "/static/audio/noot_noot.mp3"), 1000)).
							WithContext(r.Context()).
							Do(); err != nil {
							log.Print(err)
						}
					}
				}
			}
		}
	})

	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})
	http.Handle("/callback", linebotHandler)
	http.Handle("/", http.FileServer(http.FS(staticFiles)))

	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}
