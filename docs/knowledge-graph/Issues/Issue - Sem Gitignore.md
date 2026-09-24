---
type: issue
subsystem: issue
status: open
tags:
  - code-map
  - issue
---

# Issue — Sem `.gitignore`

## O quê

`__pycache__/app.cpython-314.pyc` está sendo rastreado pelo git (aparece modificado a
cada execução local). Os três `.zip` de backup (~6.8MB somados) também estão
versionados no histórico.

## Afeta

Higiene do repositório — não afeta comportamento do sistema.

## Status

Não corrigido nesta auditoria (aguardando confirmação do usuário).
