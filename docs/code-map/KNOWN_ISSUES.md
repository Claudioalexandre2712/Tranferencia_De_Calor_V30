# Problemas Conhecidos

Cada item abaixo foi confirmado por leitura direta do código em 2026-09-15. Nenhum é
especulação. Nada aqui foi corrigido automaticamente — são apenas registros, conforme
escopo desta auditoria (mapear/documentar, não alterar comportamento).

## Segurança / segredos

- **Credenciais Wi-Fi hardcoded** (`WIFI_SSID`/`WIFI_PASSWORD`) em ambos os `.ino`
  (`esp32_painel_status/esp32_painel_status.ino` e
  `esp32_monitor_ambiente/esp32_monitor_ambiente.ino`, mesmas credenciais nos dois) — SSID
  + senha em texto puro no código-fonte, versionado no git. Revalidado em 2026-09-15;
  números de linha propositalmente omitidos aqui (ver seção "Números de linha" — use
  `Grep "WIFI_SSID"` para localizar a linha atual em cada arquivo).
- **IP interno hardcoded como fallback (`SERVER_HOST`)** em ambos `.ino` — expõe topologia
  de rede interna, risco baixo mas real se o repositório for público. Revalidado em
  2026-09-15: o valor atual no código é `10.1.17.239` (não `10.18.163.204`, que era o
  valor de uma auditoria anterior e já não existe no código — puramente histórico, a rede
  do laboratório mudou de IP). `SERVER_HOST` só é usado como último recurso depois que a
  descoberta UDP e o fallback mDNS falham — ver `HARDWARE_MAP.md`. Confirme sempre por
  `Grep "SERVER_HOST"` antes de citar este valor, pois ele muda com a rede.

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
- **`app.secret_key` fixo** em `app.py:48` — só protege `flash()` no momento, mas é uma
  prática frágil se o uso do secret_key crescer.
- **`debug=True` fixo** em `app.py:1775-1777`, sem variável de ambiente controlando —
  se esse código rodar localmente exposto na rede (`host='0.0.0.0'`), o debugger do
  Werkzeug fica acessível. Mitigado em produção pelo deploy Vercel (que não usa esse
  bloco `if __name__ == '__main__'`), mas é um risco em execução local na rede do
  laboratório.
- **Handler de exceção global** (`app.py:54-72`) devolve o traceback completo em qualquer
  erro 500, para qualquer cliente — informação de diagnóstico útil em laboratório, mas
  não deveria ir para uma implantação pública sem revisão.

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

- **Sem `.gitignore`** — `__pycache__/app.cpython-314.pyc` está sendo rastreado pelo git
  (aparece como modificado a cada execução local). Os três `.zip` de backup
  (`backup_V29.zip`, `backup_completo_V30_2026-09-03.zip`,
  `backup_completo_V30_2026-09-11.zip`, ~6.8MB somados) também estão versionados no
  histórico — infla o tamanho do repositório. Não alterado nesta auditoria por estar fora
  do escopo de "mapear/documentar"; se quiser, posso criar um `.gitignore` e parar de
  versionar os `.zip` (ação reversível, mas peço confirmação antes).

## Armazenamento em memória (limitação arquitetural, não bug)

`monitoring_cache` e `temperatura_alvo_data` são dicts Python globais — sem banco de
dados nem persistência em disco. Reiniciar o Flask zera todas as leituras dos sensores.
Aceitável para o uso atual (bancada de laboratório com sessão curta), mas relevante se o
projeto crescer para ensaios longos ou histórico persistente.
