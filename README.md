# pingu-bot
Noot Noot!

## How to build?
```bash
pack build --builder=gcr.io/buildpacks/builder:v1 --publish wei840222/pingu-bot:4
```

## How to deploy?
```bash
kn ksvc apply --namespace=pingu --annotation=prometheus.io/scrape=true --annotation=prometheus.io/port=2222 --annotation=instrumentation.opentelemetry.io/inject-sdk=true --env-file=./.env --image=wei840222/pingu-bot:4 bot
```

## How to deploy by tekton?
```bash
kubectl create ns pingu
kubectl apply -k .tekton
```