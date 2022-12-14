package main

import "go.uber.org/fx"

func main() {
	fx.New(
		fx.Provide(InitMeterProvider),
		fx.Provide(InitTracerProvider),
		fx.Provide(InitGinEngine),
		fx.Invoke(RegisterLINEHandler),
		fx.Invoke(RegisterStaticFilesHandler),
	).Run()
}
