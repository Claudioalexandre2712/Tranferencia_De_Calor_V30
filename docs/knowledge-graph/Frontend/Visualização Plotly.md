---
type: component
subsystem: frontend
status: active
tags:
  - code-map
  - frontend
---

# Visualização Plotly

Gráficos de distribuição de temperatura ao longo da aleta — server-side (diferente do
Plotly.js client-side do [[Painel Status Dashboard]]).

## Responsabilidade

`gerar_grafico_temperatura_interativo`/`_multiplos_materiais` geram `(grafico_html,
dados_base)`; `extrair_dados_curvas_json_*` extrai os mesmos dados em JSON — fonte única
compartilhada entre gráfico e tabela.

## Código-fonte

`visualizacao_plotly.py`

## Recebe dados de

- [[Modelo3 - Aletas]]

## Usado em

`resultado.html`, `resultados_sele.html`
