---
type: decision
subsystem: decision
status: active
tags:
  - code-map
  - decision
---

# Decisão — Temperatura-Alvo como Referência (não controle)

## O quê

A "temperatura-alvo" configurável no [[Painel Status Dashboard]] é só um valor de
referência exibido/consultado — não há malha de controle fechado (PID/PWM) nem no
backend nem no firmware.

## Por quê (documentado explicitamente no código)

`app.py:1680-1685` documenta que o controle físico real do banho é feito pelo
termostato XH-W3002, fora do software. A temperatura-alvo serve só para o operador
acompanhar o ensaio.

## Afeta

- [[Temperatura-Alvo Backend]]
- [[Fluxo de Temperatura-Alvo]]
- [[Hardware]] (termostato XH-W3002)
