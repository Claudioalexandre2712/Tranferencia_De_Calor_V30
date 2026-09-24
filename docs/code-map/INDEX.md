# Code Map — Índice

Mapa técnico do projeto V30 (laboratório de Transferência de Calor: calculadoras Flask +
dashboard de sensores ESP32). Não leia o projeto inteiro para responder uma pergunta —
comece aqui, identifique o documento certo, abra só os arquivos necessários.

| Preciso de... | Vá para |
|---|---|
| Visão geral da arquitetura, como as peças se conectam | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Como o Flask inicializa, deploy (Vercel), entry points | [ENTRY_POINTS.md](ENTRY_POINTS.md) |
| O que cada módulo `.py` da raiz faz e quem o usa | [MODULES.md](MODULES.md) |
| Lista de todas as rotas Flask (`/api/...`, `/calculadora_...`) | [API_MAP.md](API_MAP.md) |
| Caminho sensor → firmware → backend → dashboard | [DATA_FLOW.md](DATA_FLOW.md) |
| Sensores, pinos, filtros EMA, Wi-Fi, firmware `.ino` | [HARDWARE_MAP.md](HARDWARE_MAP.md) |
| Problemas/código morto/riscos já identificados | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |

## Como navegar por pergunta

- "Onde é definida a rota X?" → [API_MAP.md](API_MAP.md)
- "Quem chama essa função de cálculo?" → [MODULES.md](MODULES.md)
- "Por que o sensor T5 não aparece no dashboard?" → [DATA_FLOW.md](DATA_FLOW.md) + [HARDWARE_MAP.md](HARDWARE_MAP.md)
- "O que muda entre ESP32 #01 e #02?" → [HARDWARE_MAP.md](HARDWARE_MAP.md)
- "Isso é código morto ou ativo?" → [KNOWN_ISSUES.md](KNOWN_ISSUES.md) (seção Código Órfão)

## Knowledge Graph (Obsidian)

`docs/knowledge-graph/` contém as mesmas informações reorganizadas como notas conectadas
por `[[wikilinks]]`, pensadas para o Graph View do Obsidian (o projeto V30 já é um vault).
Comece por `docs/knowledge-graph/00 - V30 Home.md`. Esse grafo não substitui este Code
Map — é uma camada de navegação visual por cima dele; o texto técnico detalhado continua
só aqui.

## Regra de atualização

Depois de qualquer mudança relevante em `app.py`, nos `.ino` ou nos módulos de cálculo,
rode a skill `atualizar-code-map` (`.claude/skills/atualizar-code-map/SKILL.md`) — ela usa
`git diff` para atualizar só os documentos afetados, não o Code Map inteiro.

Fonte de verdade: código > Code Map > Obsidian. Se divergirem, o código está certo — corrija
o documento.

Gerado a partir de auditoria completa do repositório em 2026-09-15.
