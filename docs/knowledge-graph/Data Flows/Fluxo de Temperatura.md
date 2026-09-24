---
type: flow
subsystem: flow
status: active
tags:
  - code-map
  - flow
---

# Fluxo de Temperatura

O fluxo principal do sistema: sensor físico → dashboard, atualizado a cada 2 segundos.

## Estágios

[[DS18B20]] / [[DHT11]]
→ [[Aquisição de Temperatura]]
→ [[Filtragem EMA]]
→ [[Calibração]]
→ [[Envio HTTP]]
→ [[POST api-temperaturas]]
→ [[monitoring_cache]]
→ [[GET-POST api-monitoramento]]
→ [[Painel Status Dashboard]]

## Componentes envolvidos

- [[ESP32 Ambiente]] (t1-t4)
- [[ESP32 Painel]] (t5-t6)
- [[Descoberta de Servidor]] (pré-requisito: o ESP32 precisa achar o IP do Flask antes)

## Debug

Ao investigar por que um valor não aparece/está errado, siga este fluxo etapa por etapa
— não leia o projeto inteiro. Ver skill `investigar-fluxo`.

## Ver também

`docs/code-map/DATA_FLOW.md`
