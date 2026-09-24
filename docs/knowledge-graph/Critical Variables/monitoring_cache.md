---
type: variable
subsystem: backend
status: active
tags:
  - code-map
  - variable
  - backend
---

# monitoring_cache

Dict Python global no processo Flask — `{t1, t2, t3, t4, t5, t6}` (+ umidade).

## Onde nasce

`app.py`, inicializado no escopo do módulo.

## Quem escreve

- [[POST api-temperaturas]] — só as chaves presentes no payload (permite os dois ESP32
  escreverem sem se sobrescrever)

## Quem lê

- [[GET-POST api-monitoramento]]
- [[GET api-status]]

## Proteção

`threading.Lock` (`monitoring_lock`) — necessário porque [[ESP32 Ambiente]] e
[[ESP32 Painel]] podem escrever concorrentemente.

## Limitação

Só em memória — reiniciar o Flask zera tudo. Ver
[[Decisão - Sem Banco de Dados]].

## Onde termina

Consumido pelo [[Painel Status Dashboard]] via polling a cada 2s.
