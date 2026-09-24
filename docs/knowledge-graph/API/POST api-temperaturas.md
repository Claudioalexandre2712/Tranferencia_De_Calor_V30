---
type: component
subsystem: api
status: active
tags:
  - code-map
  - api
  - endpoint
---

# POST /api/temperaturas

Endpoint alvo dos firmwares ESP32 — `SERVER_PATH` em ambos os `.ino`.

## Responsabilidade

`api_temperaturas` (`app.py:1603`). POST atualiza só as chaves presentes no JSON dentro
de [[monitoring_cache]] — por isso os dois ESP32 não se sobrescrevem mesmo escrevendo
concorrentemente. GET retorna `{status, temperaturas, timestamp}`.

## Código-fonte

`app.py:1603`

## Chamado por

- [[ESP32 Ambiente]] (envia t1-t4, umidade)
- [[ESP32 Painel]] (envia t5, t6)

## Escreve em

- [[monitoring_cache]]

## Fluxo

- [[Fluxo de Temperatura]]
