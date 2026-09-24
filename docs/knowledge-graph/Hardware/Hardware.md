---
type: hub
subsystem: hardware
status: active
tags:
  - code-map
  - hardware
  - hub
---

# Hardware

Componentes físicos da bancada. As notas técnicas detalhadas vivem em [[Firmware]]
(mesmos componentes, mesmo código) — este hub é só a porta de entrada pela perspectiva
física.

## Componentes

- [[ESP32 Painel]]
- [[ESP32 Ambiente]]
- [[DS18B20]]
- [[DHT11]]

## Controlador externo (sem integração de software)

Termostato **XH-W3002** — controla o banho fisicamente; a [[Temperatura-Alvo Backend]]
é só uma referência para o ensaio, sem malha de controle fechado com este componente
(ver [[Decisão - Temperatura-Alvo como Referência]]).

## Ver também

`docs/code-map/HARDWARE_MAP.md`
