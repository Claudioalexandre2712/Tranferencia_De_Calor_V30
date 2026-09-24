---
type: hub
subsystem: api
status: active
tags:
  - code-map
  - api
  - hub
---

# API

Só os 4 endpoints de monitoramento/sensores viram nós individuais — são o núcleo do
sistema em tempo real e o ponto de integração firmware↔backend↔frontend. As ~25 rotas
de calculadoras ficam agrupadas em [[Templates de Calculadoras]]/[[Backend]] para não
inflar o grafo.

## Endpoints

- [[POST api-temperaturas]]
- [[GET-POST api-monitoramento]]
- [[GET-POST api-temperatura-alvo]]
- [[GET api-status]]

## Ver também

`docs/code-map/API_MAP.md` — lista completa de todas as rotas.
