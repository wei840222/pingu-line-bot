package main

import (
	"context"
	"embed"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httptrace"
	"os"
	"path"
	"strings"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	"github.com/line/line-bot-sdk-go/v7/linebot"
	"github.com/line/line-bot-sdk-go/v7/linebot/httphandler"
	"github.com/tidwall/gjson"
	"go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	propagators_b3 "go.opentelemetry.io/contrib/propagators/b3"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.12.0"
)

//go:embed static
var staticFiles embed.FS

func joinURL(base string, paths ...string) string {
	p := path.Join(paths...)
	return fmt.Sprintf("%s/%s", strings.TrimRight(base, "/"), strings.TrimLeft(p, "/"))
}

func main() {
	exporter, err := otlptrace.New(context.Background(), otlptracegrpc.NewClient())
	if err != nil {
		log.Fatal(err)
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithSampler(sdktrace.AlwaysSample()),
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceNameKey.String("pingu-line-bot"),
			semconv.ServiceVersionKey.String("0.0.1"),
		)),
	)

	defer tp.Shutdown(context.Background())

	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{}, propagators_b3.New()))

	baseURL := os.Getenv("BASE_URL")

	linebotHandler, err := httphandler.New(
		os.Getenv("LINE_CHANNEL_SECRET"),
		os.Getenv("LINE_CHANNEL_TOKEN"),
	)
	if err != nil {
		log.Fatal(err)
	}

	bot, err := linebotHandler.NewClient(linebot.WithHTTPClient(&http.Client{Transport: otelhttp.NewTransport(http.DefaultTransport)}))
	if err != nil {
		log.Fatal(err)
	}

	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	http.Handle("/line", otelhttp.NewHandler(&LINEHandler{baseURL, bot}, "Handle LINE Bot Event"))
	http.Handle("/", otelhttp.NewHandler(http.FileServer(http.FS(staticFiles)), "Static File"))

	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}

type LINEHandler struct {
	baseURL string
	bot     *linebot.Client
}

func (h LINEHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	event, err := cloudevents.NewEventFromHTTPRequest(r)
	if err != nil {
		log.Printf("failed to parse CloudEvent from request2: %s", err)
		http.Error(w, http.StatusText(http.StatusBadRequest), http.StatusBadRequest)
		return
	}

	var events []*linebot.Event
	json.Unmarshal([]byte(gjson.GetBytes(event.Data(), "body.events").String()), &events)
	for _, event := range events {
		b, _ := json.Marshal(event)
		log.Printf("event: %s", b)
		if event.Type == linebot.EventTypeMessage {
			switch message := event.Message.(type) {
			case *linebot.TextMessage:
				if message.Text == "叫" {
					if _, err = h.bot.ReplyMessage(event.ReplyToken, linebot.NewAudioMessage(joinURL(h.baseURL, "/static/audio/noot_noot.mp3"), 1000)).
						WithContext(httptrace.WithClientTrace(r.Context(), otelhttptrace.NewClientTrace(r.Context()))).
						Do(); err != nil {
						log.Print(err)
					}
				}
			}
		}
	}
}
