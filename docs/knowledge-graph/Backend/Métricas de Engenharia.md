---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
  - calculation
---

# Métricas de Engenharia

Métricas derivadas (volume, área superficial, eficiência) e interpretação textual;
banco de materiais.

## Funções/dados principais

`calcular_metricas_engenharia`, `interpretar_metricas`; expõe `MATERIAIS_DB`,
`DICIONARIO_MATERIAIS_ID` — usado em todo o app como base central de materiais.

## Código-fonte

`metricas_engenharia.py`

## Usado por

- [[Flask App]] (`app.py:13`, reimport `app.py:1495`)
