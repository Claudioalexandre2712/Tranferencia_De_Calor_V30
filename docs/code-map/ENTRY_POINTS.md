# Entry Points

## `app.py` (raiz, ~1780 linhas)

Ponto de entrada único, local e serverless.

- `find_folder()` (`app.py:26-37`) resolve `static/`/`templates/` testando 4 candidatos
  (raiz, `V29/`, cwd, `cwd/V29`) — para funcionar tanto local quanto no Vercel.
- `app = handler = Flask(...)` (`app.py:42-47`) — o nome `handler` é o que o Vercel espera.
- `app.secret_key` hardcoded em `app.py:48` (só usado por `flash()`, sem dado sensível
  protegido por ele).
- Handler global de exceções (`app.py:54-72`) devolve página HTML com traceback completo
  em qualquer erro 500 — ver [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
- `_iniciar_auto_discovery_udp()` (`app.py:109-143`) roda em thread daemon, porta UDP 5005.
- Execução local: `app.run(debug=True, host='0.0.0.0', use_reloader=True, threaded=True)`
  (`app.py:1775-1777`) — debug=True fixo, sem variável de ambiente controlando isso.

## Deploy Vercel

- `vercel.json`: builds `app.py` via `@vercel/python`, estáticos via `@vercel/static`;
  rotas `/static/(.*)` → estáticos, `/(.*)` → `app.py`.
- `api/index.py`: handler WSGI alternativo (`from app import app`) seguindo a convenção
  de Vercel Functions em `api/*.py` — coexiste com o mapeamento direto do `vercel.json`.

## `requirements.txt`

`Flask>=3.0.0`, `Werkzeug>=3.0.0`, `Jinja2>=3.1.0`, `numpy>=1.24.0`, `scipy>=1.10.0`,
`plotly>=5.15.0`.

## Firmware (dois entry points independentes)

- `esp32_monitor_ambiente/esp32_monitor_ambiente.ino` — `setup()`/`loop()` padrão Arduino.
- `esp32_painel_status/esp32_painel_status.ino` — idem.

Detalhes de cada um: [HARDWARE_MAP.md](HARDWARE_MAP.md).
