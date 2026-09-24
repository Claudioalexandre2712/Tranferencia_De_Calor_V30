---
type: issue
subsystem: issue
status: open
tags:
  - code-map
  - issue
---

# Issue — Código Órfão

## O quê

`melhorias_sistema.py` (29KB) não é importado por nenhum módulo do projeto.
`config_otimizada.py` (14KB) só é importado por `melhorias_sistema.py` — órfão por
transitividade.

## Afeta

Nenhum componente ativo — por definição, estão fora do grafo de dependências real.

## Status

Não removido nesta auditoria — só documentado. Confirmar com o autor antes de deletar.
