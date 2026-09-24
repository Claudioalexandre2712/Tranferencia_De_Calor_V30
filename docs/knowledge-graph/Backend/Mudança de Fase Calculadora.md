---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
  - calculation
---

# Mudança de Fase Calculadora

Condensação (placa vertical, tubo horizontal) e ebulição (nucleada Rohsenow, filme
Berenson).

## Função principal

`calcular_mudanca_fase(tipo, subtipo, parametros)` — despachante único.

## Código-fonte

`mudanca_fase_calculadora.py`

## Usado por

- [[Flask App]] (rotas `/calculadora_condensacao/calcular`, `/calculadora_ebulicao/calcular`)
