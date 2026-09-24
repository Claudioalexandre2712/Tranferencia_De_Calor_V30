---
type: issue
subsystem: issue
status: open
tags:
  - code-map
  - issue
---

# Issue — Rota Morta (`/calculadora_temperaturas`)

## O quê

`calcular_com_temperaturas` (`app.py:1399`) chama
`calcular_escoamento_com_temperaturas(...)` mas descarta o resultado e sempre redireciona
para `/calculadora_escoamento_interno` (`app.py:1430`). O cálculo nunca chega ao usuário.

## Afeta

- [[Escoamento Dutos]]
- [[Flask App]]

## Status

Não corrigido nesta auditoria — parece transição inacabada.
