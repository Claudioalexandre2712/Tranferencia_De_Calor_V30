---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
  - calculation
---

# Tipos de Aletas Config

Catálogo/config dos 8 tipos de aletas suportados (campos obrigatórios/opcionais por
geometria, validação).

## Funções/dados principais

`obter_tipo_aleta`, `validar_campos_obrigatorios`, `obter_campos_formulario`,
`TIPOS_ALETAS`, `LISTA_TIPOS_ORDENADA`.

## Código-fonte

`tipos_aletas_config.py`

## Usado por

- [[Flask App]] (`app.py:18-20`, rotas de seleção/inserção de dados de aletas)
