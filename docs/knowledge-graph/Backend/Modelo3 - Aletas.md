---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
  - calculation
---

# Modelo3 — Aletas

Núcleo de cálculo de eficiência de aletas (retangular, triangular, parabólica, anular,
pino, etc.), perfis de temperatura analíticos.

## Função principal

`calcular_eficiencia(tipo_aleta, h, k, l, ...)` → `(eta, Q, A, epsilon, m, P, A_tr[, dados_didaticos])`

## Código-fonte

`modelo3.py`

## Usado por

- [[Flask App]] (`app.py:6`)
- Alimenta [[Visualização Plotly]] (mesmos dados do cálculo)

## Ver também

`docs/code-map/MODULES.md`
