---
type: component
subsystem: firmware
status: active
tags:
  - code-map
  - firmware
  - esp32
---

# ESP32 Ambiente

Firmware "#01" — lê a placa (T1-T3) e o ambiente (T4 + umidade).

## Responsabilidade

Lê 3x [[DS18B20]] com endereço ROM fixo (`ENDERECOS_SENSOR[3]`) + 1x [[DHT11]]. É o único
firmware que consulta a temperatura-alvo do servidor.

## Código-fonte

`esp32_painel_status/esp32_painel_status.ino` — **atenção:** o nome da pasta é enganoso;
confirmado por evidência executável (`doc["device"] = "esp32_01"` em
`enviarDadosParaServidor()`, mais a presença de `DHT.h`/3 endereços ROM fixos), não pelo
nome do diretório. Ver `docs/code-map/KNOWN_ISSUES.md` ("Pastas com nome trocado").

## Componentes relacionados

- [[DS18B20]]
- [[DHT11]]
- [[Aquisição de Temperatura]]
- [[Filtragem EMA]]
- [[Calibração]] (offset fixo persistido em flash)
- [[Envio HTTP]]
- [[Descoberta de Servidor]]

## Fluxos

- [[Fluxo de Temperatura]]
- [[Fluxo de Temperatura-Alvo]] (consulta `GET /api/temperatura-alvo` a cada 15s)

## Dependências

- [[POST api-temperaturas]]
- [[GET-POST api-temperatura-alvo]]

## Diferença-chave vs ESP32 Painel

Limite anti-spike 10°C; consulta temperatura-alvo; sensores com endereço ROM fixo.
