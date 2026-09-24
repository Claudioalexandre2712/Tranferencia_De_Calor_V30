---
type: flow
subsystem: flow
status: active
tags:
  - code-map
  - flow
---

# Fluxo de Temperatura-Alvo

Canal de referência para o ensaio — separado do [[Fluxo de Temperatura]], sem malha de
controle fechado.

## Estágios

[[Painel Status Dashboard]] (usuário define o valor)
→ [[GET-POST api-temperatura-alvo]]
→ [[temperatura_alvo_data]]
→ (consultado a cada 15s por) [[ESP32 Ambiente]]
→ exibido no serial/diagnóstico (não afeta o banho fisicamente)

## Decisão relacionada

- [[Decisão - Temperatura-Alvo como Referência]]
