---
type: variable
subsystem: backend
status: active
tags:
  - code-map
  - variable
  - backend
---

# temperatura_alvo_data

Dict Python global separado de [[monitoring_cache]] — `{temperatura_alvo, definida,
timestamp}`.

## Onde nasce

`app.py`, escopo do módulo, protegido por `temperatura_alvo_lock` (lock próprio,
diferente do `monitoring_lock`).

## Quem escreve

- [[GET-POST api-temperatura-alvo]] (POST do usuário via [[Painel Status Dashboard]])

## Quem lê

- [[GET-POST api-temperatura-alvo]] (GET)
- [[GET-POST api-monitoramento]] (incluído na resposta)
- [[ESP32 Ambiente]] (a cada 15s)

## Validação

Faixa física 0.0–100.0°C, converte vírgula decimal → ponto, arredonda a 4 casas.

## Fluxo

[[Fluxo de Temperatura-Alvo]]
