---
type: component
subsystem: hardware
status: active
tags:
  - code-map
  - hardware
  - firmware
---

# DHT11

Sensor de temperatura ambiente + umidade, usado só em [[ESP32 Ambiente]] (T4), pino 27.
Lido a cada 2500ms (`INTERVALO_DHT11`), com uma retentativa em caso de falha.

## Relacionados

- [[ESP32 Ambiente]]
- [[Aquisição de Temperatura]]
