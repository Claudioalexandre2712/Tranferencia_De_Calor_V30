# V30 — Laboratório de Transferência de Calor

Calculadoras de engenharia térmica (aletas, convecção, mudança de fase, arranjos de
tubos, escoamento interno) servidas por Flask, mais um dashboard em tempo real que recebe
dados de dois ESP32 com sensores de temperatura (DS18B20/DHT11) via HTTP.

## Arquitetura

- **Backend**: `app.py` (Flask, ~1780 linhas) — roteamento + cache em memória dos
  sensores. Sem banco de dados.
- **Cálculo de engenharia**: módulos separados na raiz (`modelo3.py`,
  `conveccao_calculadora.py`, `mudanca_fase_calculadora.py`, etc.) — puros, sem estado.
- **Firmware**: dois `.ino` autocontidos que enviam `POST /api/temperaturas` — **atenção:
  os nomes das pastas são enganosos** (revalidado 2026-09-15 via `doc["device"]` no JSON
  enviado, não pelo nome da pasta). `esp32_painel_status/` contém o firmware T1-T4+DHT11
  (`device: "esp32_01"`); `esp32_monitor_ambiente/` contém o firmware T5-T6
  (`device: "esp32_02"`). Ver `docs/code-map/KNOWN_ISSUES.md`.
- **Frontend**: `templates/*.html` (Jinja2) + `static/js/*`; `painel_status.html` faz
  polling em `/api/monitoramento` a cada 2s.

Detalhes completos: **consulte [docs/code-map/INDEX.md](docs/code-map/INDEX.md) antes de
reler o projeto inteiro.**

## Comandos

```bash
py app.py            # roda o Flask localmente (debug=True, porta 5000, 0.0.0.0)
pip install -r requirements.txt
```

Deploy: Vercel (`vercel.json` + `api/index.py`), automático a partir do `main`.

## Regras

- `python` não está no PATH deste ambiente (Windows) — use `py`.
- Não altere comportamento de cálculo de engenharia sem entender a fórmula/correlação
  usada no módulo correspondente (ver `docs/code-map/MODULES.md`).
- `melhorias_sistema.py` e `config_otimizada.py` são código órfão (não importados por
  `app.py`) — não assuma que estão ativos. Ver `docs/code-map/KNOWN_ISSUES.md`.
- Não hardcode novas credenciais (Wi-Fi, IP, secret) — já existem casos legados
  documentados em `docs/code-map/KNOWN_ISSUES.md`; não repita o padrão.
- Backups (`backup_*.zip`) e `__pycache__/` não são código-fonte — ignore-os ao explorar.

## Estratégia de navegação (siga esta ordem, não leia o repositório inteiro)

```
PERGUNTA
  → este CLAUDE.md (contexto geral, já leu)
  → E:\IA\Cerebro\AI-Brain\START-HERE.md (entry point canônico)
  → E:\IA\Cerebro\AI-Brain\Projetos\V30\00 V30 - Home.md
  → hub relevante no AI-Brain (Firmware, Backend, Frontend, API, Fluxos, Variáveis, Símbolos, Issues...)
  → docs/knowledge-graph/ local (LEGACY / LOCAL SUPPORTING INDEX, ver seção "Knowledge Graph" abaixo) só se
    o AI-Brain apontar para lá, faltar detalhe ainda não migrado, ou for preciso cross-check histórico
  → docs/code-map/<DOCUMENTO>.md correspondente (citado na nota do AI-Brain ou do knowledge-graph local)
  → busca (Grep) pelo símbolo/rota específica
  → só então abrir o código-fonte, no trecho indicado
```

Nunca comece por `app.py` inteiro (~1780 linhas) nem por uma busca livre no repositório.
O AI-Brain central (`Cerebro\AI-Brain\Projetos\V30`) é o hub canônico; cada nota já diz onde no
código está a resposta. O knowledge-graph local complementa quando o AI-Brain não cobre o detalhe.

**Mas o Knowledge Graph é hipótese, não fonte de verdade para fatos que podem ter
mudado.** Uma auditoria em 2026-09-15 encontrou notas com constante/valor/variável/ordem
de pipeline documentados errado, e dois firmwares com a identidade invertida em relação
ao nome da pasta (ver `docs/code-map/KNOWN_ISSUES.md`). Antes de responder com confiança
sobre constantes, valores, nomes de variáveis, endpoints, IPs, ordem de processamento ou
comportamento atual, confirme por Grep do símbolo citado na nota — não é reler o arquivo
inteiro, é uma checagem pontual. Perguntas puramente estruturais (quem depende de quem,
onde fica um componente) podem confiar direto no grafo.

**Tabela de roteamento por tipo de pergunta** (índice local de apoio — comece pelo hub
correspondente em `Cerebro\AI-Brain\Projetos\V30`; use esta tabela para o detalhe ainda
não coberto lá):

| Pergunta é sobre... | Comece em (hub) |
|---|---|
| Sensor, ESP32, filtro EMA, calibração, Wi-Fi | `docs/knowledge-graph/Firmware/Firmware.md` |
| Rota Flask, cache de sensores, módulo de cálculo | `docs/knowledge-graph/Backend/Backend.md` |
| Template, dashboard, gráfico, importação de CSV | `docs/knowledge-graph/Frontend/Frontend.md` |
| Placa/componente físico específico | `docs/knowledge-graph/Hardware/Hardware.md` |
| Endpoint específico (`/api/...`) | `docs/knowledge-graph/API/API.md` |
| Algo que atravessa múltiplos componentes ("por que X não chega em Y") | `docs/knowledge-graph/Data Flows/Fluxos de Dados.md` |
| Uma variável de estado específica (`monitoring_cache`, etc.) | `docs/knowledge-graph/Critical Variables/Variáveis Críticas.md` |
| Por que algo foi feito de um jeito (arquitetura) | `docs/knowledge-graph/Decisions/Decisões.md` |
| Bug/limitação conhecida | `docs/knowledge-graph/Issues/Problemas Conhecidos.md` |

Cada nota do grafo já linka para as notas relacionadas e para o documento certo em
`docs/code-map/` — siga os `[[wikilinks]]` em vez de adivinhar. Não copie o conteúdo do
Knowledge Graph para cá; ele é grande demais e muda com o código — leia-o sob demanda.

## Knowledge Graph (LEGACY / LOCAL SUPPORTING INDEX)

`docs/knowledge-graph/` — 51 notas conectadas (`[[wikilinks]]`), navegáveis no Graph View
do Obsidian (o projeto já é um vault) e igualmente legíveis como arquivos `.md` puros.
Não é mais o entry point canônico do projeto — esse papel é do AI-Brain central
(`Cerebro\AI-Brain\Projetos\V30\00 V30 - Home.md`, via `START-HERE.md`). Continua útil
como índice local de apoio: consulte-o quando o AI-Brain apontar para cá, quando houver
detalhe ainda não migrado para lá, ou para cross-check histórico. Complementa, não
substitui, o Code Map — as notas são curtas e apontam para `docs/code-map/*.md` quando o
detalhe técnico completo é necessário.

## Skills locais

Ver `.claude/skills/` — `analisar-backend`, `analisar-firmware`, `analisar-frontend`,
`investigar-fluxo`, `atualizar-code-map`. Todas começam pelo hub correspondente no
Knowledge Graph antes de abrir `docs/code-map/` ou o código-fonte.
