---
type: component
subsystem: firmware
status: active
tags:
  - code-map
  - firmware
  - esp32
---

# ESP32 Painel

Firmware "#02" — lê a base/água do ensaio (T5, T6).

## Responsabilidade

Lê 2x [[DS18B20]] no mesmo barramento OneWire (pino 4), descobertos por índice (sem ROM
fixo). Envia só `t5, t6` para o backend, sem tocar em t1-t4.

## Código-fonte

`esp32_monitor_ambiente/esp32_monitor_ambiente.ino` — **atenção:** o nome da pasta é
enganoso; confirmado por evidência executável (`doc["device"] = "esp32_02"` em
`enviarDadosParaServidor()`, sem `DHT.h`, 2 sensores por índice), não pelo nome do
diretório. Ver `docs/code-map/KNOWN_ISSUES.md` ("Pastas com nome trocado").

## Componentes relacionados

- [[DS18B20]]
- [[Aquisição de Temperatura]]
- [[Filtragem EMA]]
- [[Calibração]] (calibração cruzada sensor a sensor + banho de gelo, exclusiva deste firmware)
- [[Envio HTTP]]
- [[Descoberta de Servidor]]

## Fluxos

- [[Fluxo de Temperatura]]

## Dependências

- [[POST api-temperaturas]]

## Diferença-chave vs ESP32 Ambiente

Limite anti-spike 15°C (vs 10°C); não consulta temperatura-alvo; sensores descobertos
por índice, não por endereço ROM fixo.
