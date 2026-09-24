# Mapa de Rotas Flask (`app.py`)

## Sensores / monitoramento / temperatura-alvo (núcleo do sistema em tempo real)

| Rota | Método | Handler | Descrição |
|---|---|---|---|
| `/api/monitoramento` | GET/POST | `api_monitoramento` (`app.py:1551`) | Cache global `monitoring_cache` (t1-t6). POST atualiza (ou reseta com `{"reset":true}`); GET retorna cache + temperatura-alvo. Consumido por `painel_status.html` via polling a cada 2s. |
| `/painel_status` | GET | `painel_status` (`app.py:1597`) | Renderiza o dashboard em tempo real. |
| `/api/temperaturas` | GET/POST | `api_temperaturas` (`app.py:1603`) | **Endpoint alvo dos firmwares ESP32** (`SERVER_PATH` em ambos `.ino`). POST atualiza só as chaves presentes no JSON (permite os 2 ESP32 escreverem sem se sobrescrever). |
| `/api/status` | GET | `api_status` (`app.py:1655`) | Diagnóstico: status online, versão, cache atual, IP remoto. |
| `/api/temperatura-alvo` (alias `/temperatura-alvo`) | GET/POST | `api_temperatura_alvo` (`app.py:1677-1773`) | Valor de referência do ensaio (0-100°C, não é controle/PID). Consultado pelo ESP32 #01 a cada 15s; lido/escrito pelo painel. |

## Fluxo de aleta única

| Rota | Método | Handler |
|---|---|---|
| `/tipos_aletas` | GET/POST | `app.py:493` |
| `/tipos_materiais/<tipos_aletas>` | GET/POST | `app.py:500` |
| `/inserir_dados/<tipos_aletas>/<material>/<k>` | GET/POST | `app.py:509` |
| `/resultado` | GET | `app.py:585` |

## Fluxo de múltiplas aletas/materiais (`sele_*`)

| Rota | Método | Handler |
|---|---|---|
| `/sele_aleta` | GET/POST | `app.py:248` |
| `/sele_materiais` | GET/POST | `app.py:257` |
| `/inserir_seledados/<sele_aleta>/<smateriais>/<k>` | GET/POST | `app.py:272` |
| `/resultados_sele` | GET | `app.py:369` |

## Convecção (natural/forçada)

| Rota | Método | Handler |
|---|---|---|
| `/calculadora_convectivo` | GET/POST | `app.py:671`/`676` |
| `/calculadora_convectivo/<tipo>` (`natural`\|`forcada`) | GET | `app.py:695` |
| `/calculadora_convectivo/<tipo>/calcular` | POST | `calculadora_convectivo_calcular` (`app.py:705`) — detecta JSON vs form, despacha para `processar_conveccao_natural[_json]`/`processar_conveccao_forcada[_json]` |

## Mudança de fase / arranjos de tubos / escoamento interno

| Rota | Método | Handler |
|---|---|---|
| `/calculadora_condensacao` + `/calcular` | GET/POST | `app.py:1150`/`1155` |
| `/calculadora_ebulicao` + `/calcular` | GET/POST | `app.py:1206`/`1211` |
| `/calculadora_arranjos_tubos` | GET/POST | `app.py:1270`/`1274` |
| `/calculadora_escoamento_interno` | GET/POST | `app.py:1304`/`1309` — dinâmico por geometria e `tipo_calculo` |
| `/calculadora_temperaturas` | GET/POST | `app.py:1394`/`1399` — **rota legada, POST calcula mas descarta o resultado** (ver KNOWN_ISSUES) |

## Outras

| Rota | Método | Handler |
|---|---|---|
| `/` | GET | `index` (`app.py:235`) |
| `/circuito_termico`, `/circuito_termico_moderno`, `/laboratorio_termico` | GET | todas renderizam `circuito_termico_moderno.html` |
| `/calcular_circuito_termico` | POST | `app.py:1445` — só eco do JSON recebido; cálculo é client-side |
| `/calcular` | POST | `app.py:1464` — rota genérica antiga de cálculo de aleta via form |
| `/tipos_materiais` | GET | `tipos_materiais_base` (`app.py:1492`) — comparação de materiais |
| `/processar_conveccao_forcada`, `/processar_conveccao_natural`, `/processar_arranjos_tubos`, `/processar_escoamento_interno` | GET/POST | `app.py:1508-1526` — redirects de compatibilidade para as rotas atuais |

Não existe rota de importação de CSV no backend — é inteiramente client-side
(ver [DATA_FLOW.md](DATA_FLOW.md)).
