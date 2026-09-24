---
type: component
subsystem: frontend
status: active
tags:
  - code-map
  - frontend
---

# Templates de Calculadoras

Grupo dos ~14 templates Jinja2 das calculadoras (aletas, convecção, mudança de fase,
arranjos de tubos, escoamento interno) — server-rendered, não viram nós individuais
para evitar explosão do grafo.

## Código-fonte

`templates/*.html` (exceto `painel_status.html` e `circuito_termico_moderno.html`)

## Recebe dados de

- [[Flask App]]
- [[Visualização Plotly]]

## Ver também

`docs/code-map/API_MAP.md` para a lista completa de rotas associadas.
