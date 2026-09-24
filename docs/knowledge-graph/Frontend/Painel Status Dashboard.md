---
type: component
subsystem: frontend
status: active
tags:
  - code-map
  - frontend
---

# Painel Status Dashboard

Dashboard de tempo real (`painel_status.html`, ~2000+ linhas de JS embutido).

## Responsabilidade

`buscarDadosMonitoramento()` faz `fetch('/api/monitoramento')` a cada 2000ms,
`atualizarKPIs()`/`atualizarCardsTemperatura()` atualizam a UI; alimenta gráfico
Plotly.js client-side com o array `dadosTemperatura`.

## Código-fonte

`templates/painel_status.html`

## Consome

- [[GET-POST api-monitoramento]]
- [[GET-POST api-temperatura-alvo]]

## Recebe dados de

- [[Importação de CSV]] (histórico alternativo ao ao vivo)

## Fluxo

- [[Fluxo de Temperatura]]
