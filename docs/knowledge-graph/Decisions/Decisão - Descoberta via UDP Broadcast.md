---
type: decision
subsystem: decision
status: active
tags:
  - code-map
  - decision
---

# Decisão — Descoberta via UDP Broadcast

## O quê

Os ESP32 descobrem o IP do Flask via broadcast UDP (`TCC_DISCOVER_SERVER`, porta 5005)
em vez de usar um IP fixo configurado.

## Por quê (inferido do código)

A rede Wi-Fi do laboratório muda de IP; broadcast evita reconfigurar o firmware toda
vez. Existe fallback em camadas: UDP → mDNS → IP fixo hardcoded (último recurso).

## Afeta

- [[Descoberta de Servidor]]
- [[ESP32 Ambiente]]
- [[ESP32 Painel]]
- [[Flask App]] (`_iniciar_auto_discovery_udp`)
