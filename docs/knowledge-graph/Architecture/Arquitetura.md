---
type: hub
subsystem: core
status: active
tags:
  - code-map
  - architecture
  - hub
---

# Arquitetura

Dois subsistemas cruzando um único backend Flask: calculadoras de engenharia térmica
(síncronas, sem estado) e monitoramento de bancada em tempo real (ESP32 → cache em
memória → dashboard por polling).

## Componentes

- [[Firmware]] — leitura, filtro e envio dos sensores
- [[Backend]] — roteamento Flask, cache, módulos de cálculo
- [[Frontend]] — templates e dashboard
- [[Hardware]] — sensores e placas físicas

## Decisões que moldaram esta arquitetura

- [[Decisão - Sem Banco de Dados]]
- [[Decisão - Descoberta via UDP Broadcast]]
- [[Decisão - Temperatura-Alvo como Referência]]

## Ver também

`docs/code-map/ARCHITECTURE.md` (diagrama completo), `docs/code-map/ENTRY_POINTS.md`.
