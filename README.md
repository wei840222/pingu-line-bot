# pingu-line-bot
Noot Noot!

## How to build?
```bash
pack build --builder=gcr.io/buildpacks/builder:v1 --publish wei840222/pingu-line-bot:1
```

## How to deploy?
```bash
kn ksvc apply --namespace=pingu --image=wei840222/pingu-line-bot:1 --env-file=./.env line-bot
```