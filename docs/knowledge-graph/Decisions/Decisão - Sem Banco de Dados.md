---
type: decision
subsystem: decision
status: active
tags:
  - code-map
  - decision
---

# Decisão — Sem Banco de Dados

## O quê

[[monitoring_cache]] e [[temperatura_alvo_data]] são dicts Python globais, só em memória
— sem persistência em disco, sem banco de dados.

## Por quê (inferido do escopo do projeto)

Bancada de laboratório com sessões curtas de ensaio, não produção contínua — reiniciar o
servidor entre ensaios é aceitável.

## Consequência

Reiniciar o Flask zera todas as leituras. Se o projeto crescer para ensaios longos ou
histórico persistente, isso precisa mudar.

## Afeta

- [[Backend]]
- [[Fluxo de Temperatura]]
