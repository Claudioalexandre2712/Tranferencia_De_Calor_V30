---
type: component
subsystem: firmware
status: active
tags:
  - code-map
  - firmware
  - algorithm
---

# Filtragem EMA

Filtro de média móvel exponencial aplicado a cada leitura válida, em ambos os firmwares.
**Revalidado em 2026-09-15 contra a sequência real de atribuições no código** (não contra
o comentário de cabeçalho isolado) — ver `docs/code-map/HARDWARE_MAP.md`.

## Pipeline real (confirmado pela ordem das atribuições, idêntico nos dois firmwares)

```
Raw (leitura física) → Anti-Spike (leituraValida) → Calibração (offset) → EMA → Final
```

A calibração acontece **antes** do EMA, não depois — `temperaturasCalibradas[i]` é
calculada e só então usada como entrada do EMA.

## Fórmula

```
temperaturasCalibradas[i] = temperaturasRaw[i] + OFFSETS_DS18B20[i]
temperaturasFiltradas[i] = ALPHA_EMA * temperaturasCalibradas[i] + (1 - ALPHA_EMA) * temperaturasFiltradas[i]
```

`ALPHA_EMA = 0.20f` (mesma constante nos dois firmwares; comentário no código explica:
`alpha = Δt / (tau + Δt) = 1s / (4s + 1s) = 0.20`).

Na primeira leitura válida (antes de `emaIniciado[i]` ser `true`), o filtro não usa a
fórmula acima — inicializa direto: `temperaturasFiltradas[i] = temperaturasCalibradas[i]`
(evita partir de zero).

## Atua sobre

- [[temperaturasFiltradas]]

## Depende de

- [[Aquisição de Temperatura]] (só aplica a leituras que passaram em `leituraValida()`)
- [[Calibração]] (a entrada do EMA já vem com offset aplicado)

## Seguido por

- [[Envio HTTP]] (`temperaturas[i] = temperaturasFiltradas[i]` é o valor final enviado)

## Ver também

`docs/code-map/HARDWARE_MAP.md`

## Nota de correção

Uma versão anterior desta nota citava `FATOR_FILTRO_EMA = 0.25` sobre uma variável
`leiturasBrutasFiltradas`, e descrevia a calibração como posterior ao EMA — nenhum dos
dois nomes existe no código atual, e a ordem estava invertida. Corrigido em 2026-09-15
após revalidação linha a linha nos dois `.ino`. Ver
`docs/knowledge-graph/Critical Variables/temperaturasFiltradas.md` (nota renomeada, com
alias para o nome antigo).
