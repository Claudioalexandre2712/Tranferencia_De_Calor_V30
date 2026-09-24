---
type: issue
subsystem: issue
status: open
tags:
  - code-map
  - issue
  - security
---

# Issue — Credenciais Hardcoded

## O quê

SSID e senha de Wi-Fi em texto puro, versionados no git, em ambos os `.ino`.

## Onde

`esp32_monitor_ambiente/esp32_monitor_ambiente.ino:37-38`,
`esp32_painel_status/esp32_painel_status.ino:35-36`. IP interno de fallback também
hardcoded (`SERVER_HOST`, linha 40/38 respectivamente).

## Afeta

- [[ESP32 Ambiente]]
- [[ESP32 Painel]]

## Status

Não corrigido nesta auditoria — só documentado.
