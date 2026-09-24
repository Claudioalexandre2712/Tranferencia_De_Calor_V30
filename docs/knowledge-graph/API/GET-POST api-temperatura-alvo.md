---
type: component
subsystem: api
status: active
tags:
  - code-map
  - api
  - endpoint
---

# GET/POST /api/temperatura-alvo

Alias: `/temperatura-alvo`.

## Responsabilidade

[[Temperatura-Alvo Backend]] (`app.py:1677-1773`) — valor de referência 0-100°C, não é
controle/PID.

## Chamado por

- [[ESP32 Ambiente]] (GET, a cada 15s, só diagnóstico)
- [[Painel Status Dashboard]] (GET para exibir, POST para configurar)

## Escreve/lê

- [[temperatura_alvo_data]]

## Fluxo

- [[Fluxo de Temperatura-Alvo]]
