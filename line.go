package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptrace"
	"net/url"
	"os"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	"github.com/gin-gonic/gin"
	"github.com/line/line-bot-sdk-go/v7/linebot"
	"github.com/tidwall/gjson"
	"go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

type lineHandler struct {
	linebot *linebot.Client
}

func (h lineHandler) callback(c *gin.Context) {
	ce, err := cloudevents.NewEventFromHTTPRequest(c.Request)
	if err != nil {
		c.Error(err)
		c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{
			"error": err,
		})
		return
	}

	span := trace.SpanFromContext(c)
	span.AddEvent("Parse CloudEvent", trace.WithAttributes(attribute.String("cloudevent", ce.String())))

	var events []*linebot.Event
	if err := json.Unmarshal([]byte(gjson.GetBytes(ce.Data(), "body.events").Raw), &events); err != nil {
		c.Error(err)
		c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{
			"error": err,
		})
		return
	}

	for _, e := range events {
		if e.Type == linebot.EventTypeMessage {
			switch message := e.Message.(type) {
			case *linebot.TextMessage:
				if message.Text == "叫" {
					audioURL, err := url.JoinPath(os.Getenv("BASE_URL"), "/static/audio/noot_noot.mp3")
					if err != nil {
						c.Error(err)
						continue
					}
					if _, err = h.linebot.ReplyMessage(e.ReplyToken, linebot.NewAudioMessage(audioURL, 1000)).
						WithContext(httptrace.WithClientTrace(c, otelhttptrace.NewClientTrace(c))).
						Do(); err != nil {
						c.Error(err)
					}
				}
			}
		}
	}

}

func RegisterLINEHandler(e *gin.Engine) error {
	bot, err := linebot.New(
		os.Getenv("LINE_CHANNEL_SECRET"),
		os.Getenv("LINE_CHANNEL_TOKEN"),
		linebot.WithHTTPClient(&http.Client{Transport: otelhttp.NewTransport(http.DefaultTransport)}),
	)
	if err != nil {
		return err
	}

	h := &lineHandler{bot}
	e.POST("/line", h.callback)
	return nil
}
