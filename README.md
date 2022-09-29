# pingu-line-bot
Noot Noot!

## How to build?
```bash
pack build --builder=gcr.io/buildpacks/builder:v1 --publish wei840222/pingu-line-bot:3
```

## How to deploy?
```bash
kn ksvc apply --namespace=pingu --image=wei840222/pingu-line-bot:3 --env-file=./.env --annotation=instrumentation.opentelemetry.io/inject-sdk=true line-bot
```