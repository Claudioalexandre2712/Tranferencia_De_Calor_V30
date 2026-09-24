---
type: component
subsystem: firmware
status: active
tags:
  - code-map
  - firmware
  - network
---

# Descoberta de Servidor

Mecanismo pelo qual os ESP32 encontram o IP do Flask sem configuração fixa — a rede
Wi-Fi do laboratório muda, então o IP não pode ser hardcoded como única fonte.

## Como funciona

1. Broadcast UDP `"TCC_DISCOVER_SERVER"` na porta 5005 (`buscarServidorAutomatico()`).
2. [[Flask App]] responde `"TCC_SERVER_IP:<porta>"` via `_iniciar_auto_discovery_udp`.
3. Fallback: mDNS (`GalaxyBook4Pro.local`), depois `SERVER_HOST` (IP fixo hardcoded,
   usado só como último recurso — **não confundir com o IP descoberto dinamicamente**
   via UDP, que é o caminho normal). O valor de `SERVER_HOST` muda com a rede do
   laboratório; confirme por `Grep "SERVER_HOST"` em vez de citar de memória — ver
   `docs/code-map/KNOWN_ISSUES.md`.
4. Redescoberta automática após 3 falhas HTTP consecutivas.

## Relacionados

- [[ESP32 Painel]]
- [[ESP32 Ambiente]]
- [[Flask App]]
- [[Decisão - Descoberta via UDP Broadcast]]

## Ver também

`docs/code-map/ARCHITECTURE.md` (seção "Descoberta de rede")
