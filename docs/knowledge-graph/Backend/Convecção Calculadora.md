---
type: component
subsystem: backend
status: active
tags:
  - code-map
  - backend
  - calculation
---

# Convecção Calculadora

Correlações de convecção natural (placa vertical/horizontal, cilindro, esfera) e forçada
(placa, cilindro cruzado, tubo interno).

## Função principal

`calcular_coeficiente_convectivo(tipo, geometria, parametros)` — único ponto de entrada.

## Código-fonte

`conveccao_calculadora.py`

## Particularidade

Importado **localmente** dentro das funções de `app.py` (`app.py:735,822,978,1082`), não
no topo do arquivo — padrão deliberadamente diferente dos outros módulos.

## Usado por

- [[Flask App]]
