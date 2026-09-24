---
type: component
subsystem: firmware
status: active
tags:
  - code-map
  - firmware
---

# Calibração

Dois mecanismos diferentes, um em cada firmware.

## Em [[ESP32 Ambiente]]

Offset fixo por sensor, persistido em flash via `Preferences`:
`OFFSETS_DS18B20[3] = {0.0000, 2.7500, 3.5042}`.

## Em [[ESP32 Painel]]

- `calibrarSensor5ComSensor6()` — calibração cruzada ao vivo via comando serial `'C'`.
- `calibrarSensoresGelo()` — calibração absoluta em banho de gelo (30 amostras).

## Relacionados

- [[DS18B20]]
- [[Filtragem EMA]] (offset aplicado **antes** do EMA — revalidado 2026-09-15 pela ordem
  real das atribuições no código: `temperaturasCalibradas[i] = temperaturasRaw[i] +
  OFFSETS_DS18B20[i]` acontece antes de `temperaturasFiltradas[i] = ALPHA_EMA * ...`)
