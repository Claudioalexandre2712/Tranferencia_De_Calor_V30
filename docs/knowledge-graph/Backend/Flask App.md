---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
---

# Flask App

Ponto de entrada único do backend, local e serverless (Vercel).

## Responsabilidade

Roteamento de todas as rotas, inicialização (`find_folder` resolve `static/`/`templates/`
em 4 candidatos), thread de [[Descoberta de Servidor]] em UDP 5005, handler global de
exceções (traceback completo em qualquer 500).

## Código-fonte

`app.py` (~1780 linhas)

## Contém

- [[Cache de Monitoramento]]
- [[Temperatura-Alvo Backend]]

## Expõe

- [[POST api-temperaturas]]
- [[GET-POST api-monitoramento]]
- [[GET-POST api-temperatura-alvo]]
- [[GET api-status]]

## Chama

- [[Modelo3 - Aletas]], [[Convecção Calculadora]], [[Mudança de Fase Calculadora]],
  [[Arranjos de Tubos]], [[Escoamento Dutos]]

## Ver também

`docs/code-map/ENTRY_POINTS.md`
