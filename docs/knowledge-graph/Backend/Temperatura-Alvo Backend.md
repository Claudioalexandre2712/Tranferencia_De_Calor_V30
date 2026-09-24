---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
---

# Temperatura-Alvo (Backend)

Canal separado do cache de sensores — valor de referência do ensaio, não um setpoint de
controle.

## Responsabilidade

`api_temperatura_alvo` (`app.py:1677-1773`) gerencia [[temperatura_alvo_data]]: aceita
JSON ou form, converte vírgula decimal → ponto, valida faixa física 0.0–100.0°C,
arredonda a 4 casas.

## Código-fonte

`app.py:1677-1773`

## Exposto por

- [[GET-POST api-temperatura-alvo]]

## Consultado por

- [[ESP32 Ambiente]] (a cada 15s, só para exibição/diagnóstico)

## Fluxo

- [[Fluxo de Temperatura-Alvo]]

## Decisão relacionada

- [[Decisão - Temperatura-Alvo como Referência]]
