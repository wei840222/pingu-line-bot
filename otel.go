package main

import (
	"context"

	propagators_b3 "go.opentelemetry.io/contrib/propagators/b3"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	otelprom "go.opentelemetry.io/otel/exporters/prometheus"
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/propagation"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.12.0"
	"go.opentelemetry.io/otel/trace"
	"go.uber.org/fx"
)

var (
	tracer trace.Tracer
	meter  metric.Meter
)

func InitMeterProvider(lc fx.Lifecycle) (metric.MeterProvider, error) {
	exporter, err := otelprom.New()
	if err != nil {
		return nil, err
	}

	provider := sdkmetric.NewMeterProvider(sdkmetric.WithReader(exporter))

	meter = provider.Meter("github.com/wei840222/pingu-bot")

	lc.Append(fx.Hook{
		OnStop: func(ctx context.Context) error {
			return provider.Shutdown(ctx)
		},
	})

	return provider, nil
}

func InitTracerProvider(lc fx.Lifecycle) (trace.TracerProvider, error) {
	exporter := otlptrace.NewUnstarted(otlptracegrpc.NewClient())

	provider := sdktrace.NewTracerProvider(
		sdktrace.WithSampler(sdktrace.AlwaysSample()),
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceNameKey.String("pingu-bot"),
			semconv.ServiceVersionKey.String("1.0.0"),
		)),
	)

	tracer = provider.Tracer("github.com/wei840222/pingu-bot")

	otel.SetTracerProvider(provider)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{}, propagators_b3.New()))

	lc.Append(fx.Hook{
		OnStart: func(ctx context.Context) error {
			return exporter.Start(ctx)
		},
		OnStop: func(ctx context.Context) error {
			return provider.Shutdown(ctx)
		},
	})

	return provider, nil
}
