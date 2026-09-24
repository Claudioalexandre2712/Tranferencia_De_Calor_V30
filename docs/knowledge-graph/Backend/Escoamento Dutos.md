---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
  - calculation
---

# Escoamento Dutos

Escoamento interno generalizado (circular/quadrado/retangular), diâmetro hidráulico.

## Funções principais

- `escoamento_interno_duto(parametros)` — cálculo tradicional
- `calcular_h_com_temperaturas(parametros)` — tipo `temp_entrada_saida`
- `calcular_escoamento_com_temperaturas(...)` — usado pela rota legada (resultado
  descartado, ver [[Issue - Rota Morta]])

## Código-fonte

`escoamento_dutos.py`

## Usado por

- [[Flask App]] (`/calculadora_escoamento_interno`, `/calculadora_temperaturas`)
