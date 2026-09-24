---
type: component
subsystem: firmware
status: active
tags:
  - code-map
  - firmware
  - network
---

# Envio HTTP

Envio periódico (a cada 2000ms, `INTERVALO_ENVIO`) das leituras filtradas para o backend.

## Responsabilidade

Monta um JSON (`ArduinoJson`) com as chaves do próprio firmware — `t1,t2,t3,t4,umidade`
em [[ESP32 Ambiente]], `t5,t6` em [[ESP32 Painel]] — mais `device` e `timestamp`, e faz
`HTTPClient.POST` para o endpoint de temperaturas.

## Recebe de

- [[Filtragem EMA]] / [[temperaturasFiltradas]]
- [[Calibração]]

## Envia para

- [[POST api-temperaturas]]

## Depende de

- [[Descoberta de Servidor]] (para saber o IP do backend)
