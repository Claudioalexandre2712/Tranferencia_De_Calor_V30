---
type: hub
subsystem: variable
status: active
tags:
  - code-map
  - variable
  - hub
---

# Variáveis Críticas

Só variáveis que atravessam módulos/camadas viram nós — não parâmetros locais de função.

## Variáveis

- [[monitoring_cache]] — estado global do backend, sensores t1-t6
- [[temperatura_alvo_data]] — estado global do backend, canal de referência
- [[temperaturasFiltradas]] — buffer no firmware, saída do filtro EMA

## Ver também

`docs/code-map/DATA_FLOW.md`
