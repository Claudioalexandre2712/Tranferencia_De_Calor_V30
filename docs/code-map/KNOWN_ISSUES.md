# Problemas Conhecidos

Cada item abaixo foi confirmado por leitura direta do código em 2026-09-15. Nenhum é
especulação. Nada aqui foi corrigido automaticamente — são apenas registros, conforme
escopo desta auditoria (mapear/documentar, não alterar comportamento).

## Segurança / segredos

Revisão de segurança para publicação (2026-09-29) — itens abaixo **corrigidos**:

- **Credenciais Wi-Fi**: saíram dos `.ino`; agora vêm de `secrets.h` (no `.gitignore`), com
  modelo em `secrets.example.h` em cada pasta de firmware. A senha antiga foi trocada no
  roteador e removida do histórico do git.
- **`app.secret_key`**: vem de `FLASK_SECRET_KEY` (variável de ambiente); sem ela, chave
  aleatória por processo.
- **`debug=True` fixo**: agora só com `FLASK_DEBUG=1`.
- **Handler de exceção global**: não devolve mais traceback nem texto da exceção ao público
  (só com debug), escapa tudo e deixa erros HTTP (404/405/400) passarem com o código certo.
  Antes, `/resultado?h=<script>…` refletia o payload sem escape (XSS).
- **XSS em `resultados_sele`**: `dados_grafico_json` usa `htmlsafe_json_dumps`, então um
  nome de material com `</script>` não quebra mais o bloco `<script>`.
- **`polyfill.io`** (domínio comprometido em 2024) removido de dois templates.
- **Gravação anônima de sensores**: na Vercel (`VERCEL=1`) os `POST` de
  `/api/temperaturas`, `/api/monitoramento` e `/api/temperatura-alvo` respondem 403.
- **CSP com nonce** + cabeçalhos de segurança (`app.py:add_security_headers` e
  `vercel.json`). Atributos `on*=` viraram `data-on*=`, tratados por
  `static/js/csp-handlers.js`. Ver README, seção "Segurança do site".

Ainda aberto:

- **IP interno como fallback (`SERVER_HOST`)** nos dois `.ino` — IP privado da rede do
  laboratório; risco baixo. Confirme sempre por `Grep "SERVER_HOST"` antes de citar o valor.
  `SERVER_HOST` só é usado depois que a descoberta UDP e o fallback mDNS falham — ver
  `HARDWARE_MAP.md`.
- **`innerHTML` com texto do usuário no circuito térmico** (nomes de camadas/variantes,
  inclusive de JSON importado): só afeta o próprio usuário e a CSP bloqueia a execução de
  script, mas trocar por `textContent` seria o ideal.
- **Relatórios `static/relatorio.txt` / `selerelatorio.txt`** são sobrescritos a cada
  cálculo e servidos publicamente (último cálculo de qualquer visitante). Na Vercel o disco é
  somente leitura, então a gravação falha em silêncio.

## Pastas com nome trocado em relação ao conteúdo

- **`esp32_monitor_ambiente/` e `esp32_painel_status/` não correspondem ao seu conteúdo.**
  Revalidado em 2026-09-15 com evidência executável (não só comentário de cabeçalho):
  contagem de sensores inicializados, presença/ausência de `DHT.h`, e o campo literal
  `doc["device"]` montado no JSON enviado ao backend.
  - `esp32_painel_status/esp32_painel_status.ino` contém na verdade o firmware **"ESP32
    #01"** (3x DS18B20 + DHT11, T1-T4, `doc["device"] = "esp32_01"`) — o que a
    documentação anterior chamava de "ESP32 Ambiente".
  - `esp32_monitor_ambiente/esp32_monitor_ambiente.ino` contém na verdade o firmware
    **"ESP32 #02"** (2x DS18B20, T5-T6, `doc["device"] = "esp32_02"`) — o que a
    documentação anterior chamava de "ESP32 Painel".
  - Isso não é um bug de comportamento (o sistema funciona corretamente — o backend não
    depende do nome da pasta, só do campo `device` e das chaves `t1..t6` no JSON) — é só
    uma inconsistência de nomenclatura entre a estrutura de diretórios e a função real de
    cada firmware. **Código não alterado nesta auditoria** (fora de escopo: renomear
    pastas/arquivos `.ino` é uma mudança estrutural que afeta a compilação Arduino,
    exige confirmação explícita do usuário antes de ser feita).
  - Documentação corrigida para citar o arquivo real por função (`doc["device"]`) em vez
    de confiar no nome da pasta: `HARDWARE_MAP.md`, `docs/knowledge-graph/Firmware/ESP32
    Ambiente.md`, `docs/knowledge-graph/Firmware/ESP32 Painel.md`.
## Código órfão / não integrado

- **`melhorias_sistema.py`** (29KB) — nenhum módulo do projeto o importa (nem `app.py`
  nem outro `.py` da raiz). Parece um módulo experimental abandonado.
- **`config_otimizada.py`** (14KB) — só é importado por `melhorias_sistema.py`, que por
  sua vez não é importado por ninguém. Órfão por transitividade.
- **`escoamento_interno.py`** — importado em `app.py:16`, mas nenhuma chamada direta de
  `escoamento_interno_tubo_circular` foi encontrada nas rotas ativas (o fluxo real de
  escoamento interno usa `escoamento_dutos.py`). Pode ser legado mantido por segurança.

## Rota morta/incompleta

- **`POST /calculadora_temperaturas`** (`calcular_com_temperaturas`, `app.py:1399`) chama
  `calcular_escoamento_com_temperaturas(...)` mas descarta o resultado e sempre faz
  `redirect(url_for('calculadora_escoamento_interno'))` (`app.py:1430`). O cálculo feito
  nessa função nunca chega ao usuário — parece uma rota de transição inacabada.

## Higiene de repositório

- **`.gitignore` criado** (2026-09-29): ignora `.env*`, `secrets.h`, `__pycache__/`,
  `backup_*.zip`, `node_modules/`, builds e `.DS_Store`. `__pycache__/` deixou de ser
  versionado e os `.zip` de backup foram removidos do repositório e do histórico.

## Armazenamento em memória (limitação arquitetural, não bug)

`monitoring_cache` e `temperatura_alvo_data` são dicts Python globais — sem banco de
dados nem persistência em disco. Reiniciar o Flask zera todas as leituras dos sensores.
Aceitável para o uso atual (bancada de laboratório com sessão curta), mas relevante se o
projeto crescer para ensaios longos ou histórico persistente.
