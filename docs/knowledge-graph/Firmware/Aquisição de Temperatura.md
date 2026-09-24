---
type: component
subsystem: firmware
status: active
tags:
  - code-map
  - firmware
---

# Aquisição de Temperatura

Leitura assíncrona (não bloqueante) dos sensores, comum aos dois firmwares.

## Responsabilidade

- [[DS18B20]]: conversão 12-bit não bloqueante (função `processarLeiturasAssincronas()`),
  espera `TEMPO_CONVERSAO_12BITS=750ms`.
- [[DHT11]]: leitura a cada 2500ms (função `processarLeituraDHT11()`), só em
  [[ESP32 Ambiente]].
- Validação anti-spike/desconexão antes de aceitar a leitura (função `leituraValida()`).

## Código-fonte

Funções `processarLeiturasAssincronas()` e `leituraValida()`, presentes nos dois
firmwares (mesma lógica, thresholds de anti-spike diferentes — ver
[[ESP32 Ambiente]]/[[ESP32 Painel]] para qual arquivo real corresponde a qual). A leitura
de DHT11 (`processarLeituraDHT11()`) existe só no arquivo do ESP32 #01. Números de linha
propositalmente omitidos aqui — confirme por `Grep "processarLeiturasAssincronas"` no
arquivo relevante, pois linhas mudam com pequenas edições. Detalhe completo:
`docs/code-map/HARDWARE_MAP.md`.

## Alimenta

- [[Filtragem EMA]]
- [[temperaturasFiltradas]]

## Ver também

`docs/code-map/HARDWARE_MAP.md`, `docs/code-map/DATA_FLOW.md`
