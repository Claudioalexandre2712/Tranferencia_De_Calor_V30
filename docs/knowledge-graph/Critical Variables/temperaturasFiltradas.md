---
type: variable
subsystem: firmware
status: active
tags:
  - code-map
  - variable
  - firmware
aliases:
  - leiturasBrutasFiltradas
---

# temperaturasFiltradas

Array/buffer no firmware (ambos os `.ino`, um por dispositivo) — saída do filtro EMA
aplicado a cada sensor. **Renomeado em 2026-09-15**: o nome anterior desta nota,
`leiturasBrutasFiltradas`, não corresponde a nenhuma variável do código atual — foi uma
suposição não verificada de uma auditoria anterior. Confirmado por leitura direta:
`float temperaturasFiltradas[NUM_SENSORES]`, declarado no topo de cada `.ino`. Alias
mantido em YAML só para rastreabilidade histórica desta correção, não porque o nome
antigo tenha existido no código.

## Onde nasce

Declarada como array global em cada firmware; populada dentro de
`processarLeiturasAssincronas()`, depois de [[Aquisição de Temperatura]] validar a
leitura (`leituraValida()`) e de [[Calibração]] aplicar o offset.

## Transformação

`temperaturasFiltradas[i] = ALPHA_EMA * temperaturasCalibradas[i] + (1 - ALPHA_EMA) * temperaturasFiltradas[i]`
— ver [[Filtragem EMA]] para o pipeline completo e a ordem real (calibração antes do EMA).

## Quem lê/usa depois

- `temperaturas[i] = temperaturasFiltradas[i]` — valor final usado para exibição serial e
  telemetria.
- [[Envio HTTP]] (monta o JSON enviado ao backend a partir de `temperaturas[i]`).

## Onde termina

Vira `t1..t6` no JSON de [[POST api-temperaturas]], depois [[monitoring_cache]].
