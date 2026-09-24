---
type: component
subsystem: api
status: active
tags:
  - code-map
  - api
  - endpoint
---

# GET/POST /api/monitoramento

Endpoint consumido pelo dashboard.

## Responsabilidade

`api_monitoramento` (`app.py:1551`). POST atualiza [[monitoring_cache]] (ou zera tudo com
`{"reset":true}`). GET retorna o cache + temperatura-alvo.

## Código-fonte

`app.py:1551`

## Consumido por

- [[Painel Status Dashboard]] (polling a cada 2000ms)

## Lê de

- [[monitoring_cache]]
- [[temperatura_alvo_data]]
