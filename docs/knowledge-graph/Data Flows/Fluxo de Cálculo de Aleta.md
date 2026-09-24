---
type: flow
subsystem: flow
status: active
tags:
  - code-map
  - flow
---

# Fluxo de Cálculo de Aleta

Fluxo síncrono das calculadoras — sem sensores, sem estado persistente, um request por
cálculo.

## Estágios

[[Templates de Calculadoras]] (formulário do usuário)
→ [[Flask App]] (rota, validação de campos via [[Tipos de Aletas Config]])
→ [[Modelo3 - Aletas]] (`calcular_eficiencia`)
→ [[Métricas de Engenharia]] (`calcular_metricas_engenharia`, `interpretar_metricas`)
→ [[Visualização Plotly]] (gráfico + JSON, mesma fonte de dados)
→ [[Templates de Calculadoras]] (renderização do resultado)

## Variante multi-material/multi-tipo

Mesma cadeia, mas itera sobre combinações (rota `/resultados_sele`), usando
`gerar_grafico_temperatura_multiplos_materiais`.
