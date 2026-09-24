---
type: component
subsystem: frontend
status: active
tags:
  - code-map
  - frontend
---

# Importação de CSV

Duas implementações independentes, **100% client-side** — não existe endpoint Flask para
isso.

## Onde

- `painel_status.html:1683` `carregarArquivoCSV(event)` — popula histórico do gráfico do
  painel.
- `calculadora_natural.html:651` `carregarCSVNatural(event)` — popula campos da
  calculadora de convecção natural; `aplicarModoCSV()` escolhe modo de agregação
  (último ponto / todos / últimos 15% = "regime permanente").

## Alimenta

- [[Painel Status Dashboard]]
- [[Convecção Calculadora]] (indiretamente, via formulário preenchido)
