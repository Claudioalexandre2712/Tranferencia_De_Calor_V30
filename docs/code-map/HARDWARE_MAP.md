# Mapa de Hardware / Firmware

> **Nota sobre nomes de pasta (revalidado em 2026-09-15):** os nomes das pastas
> `esp32_monitor_ambiente/` e `esp32_painel_status/` **não correspondem** ao conteúdo real
> dos `.ino` que contêm. Confirmado por evidência executável (não só comentário):
> quantidade de sensores inicializados, presença/ausência de `DHT.h`/`dht.begin()`, e o
> campo `doc["device"]` literalmente montado no JSON enviado ao backend.
> Ver [KNOWN_ISSUES.md](KNOWN_ISSUES.md#pastas-com-nome-trocado-em-relação-ao-conteúdo).
> Esta documentação identifica cada firmware pela função real (device id / sensores),
> não pelo nome da pasta — sempre cite o caminho completo do arquivo, nunca assuma pelo
> nome da pasta sozinho.

## ESP32 #01 — "Placa e Ambiente" (`doc["device"] = "esp32_01"`)

**Arquivo real:** `esp32_painel_status/esp32_painel_status.ino` (confirmado via
`doc["device"] = "esp32_01"` na função `enviarDadosParaServidor()`).

- **Sensores**: 3x DS18B20 em OneWire único (`ONE_WIRE_PIN 4`), endereços ROM fixos em
  `ENDERECOS_SENSOR[3]` → T1 (início da placa), T2 (centro), T3 (fim); 1x DHT11
  (`DHT_PIN 27`, biblioteca `DHT.h` incluída neste arquivo) → T4 (ambiente) + umidade.
- **Leitura**: função `processarLeiturasAssincronas()` — conversão 12-bit não bloqueante,
  espera `TEMPO_CONVERSAO_12BITS=750ms`; função `processarLeituraDHT11()` a cada
  `INTERVALO_DHT11=2500ms`.
- **Validação/filtro**: função `leituraValida()` — descarta desconectado/`85.0`/fora de
  `[-40,130]°C`/salto >10°C.
- **Calibração**: offset fixo por sensor `OFFSETS_DS18B20[3] = {0.0000, 2.7500, 3.5042}`,
  persistido em flash (`Preferences`) — aplicado **antes** do EMA (ver
  [[Filtragem EMA]] no Knowledge Graph para o pipeline completo, revalidado contra o
  código real).
- **Temperatura-alvo**: função `consultarTemperaturaAlvoServidor()`, a cada
  `INTERVALO_CONSULTA_ALVO=15000ms` — só leitura/diagnóstico, sem malha de controle.
- **Envio**: função `enviarDadosParaServidor()`, a cada `INTERVALO_ENVIO=2000ms`,
  `POST /api/temperaturas` com `t1,t2,t3,t4,umidade,device:"esp32_01",timestamp`.
- **Descoberta de servidor**: função `buscarServidorAutomatico()` — UDP broadcast porta
  5005; fallback mDNS (`GalaxyBook4Pro.local`), depois `SERVER_HOST` (IP fixo, ver seção
  "IP de fallback" abaixo). Redescoberta automática após 3 falhas HTTP seguidas.
- **Wi-Fi**: SSID/senha hardcoded (`WIFI_SSID`/`WIFI_PASSWORD`, início do arquivo) — ver
  [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
- LED onboard (GPIO 2): piscando = conectando Wi-Fi; 1 pulso/2s = envio OK; 2 pulsos
  rápidos = erro. Menu serial: `'A'`/`'C'`/`'G'`/`'R'`/`'S'`.

## ESP32 #02 — "Base e Água" (`doc["device"] = "esp32_02"`)

**Arquivo real:** `esp32_monitor_ambiente/esp32_monitor_ambiente.ino` (confirmado via
`doc["device"] = "esp32_02"` na função `enviarDadosParaServidor()`).

- **Sensores**: 2x DS18B20 (T5, T6 — base/água), mesmo pino OneWire 4, descobertos por
  índice (função `descobrirSensores()`, sem ROM fixo). Sem DHT11 neste arquivo.
- **Leitura/filtro**: mesma arquitetura assíncrona 12-bit + anti-spike (salto >15°C,
  função `leituraValida()`) + EMA (ver [[Filtragem EMA]]).
- **Calibração cruzada**: função `calibrarSensor5ComSensor6()` via comando serial `'C'`;
  função `calibrarSensoresGelo()` — calibração absoluta em banho de gelo (30 amostras).
- **Envio**: função `enviarDadosParaServidor()` — só `t5, t6, device:"esp32_02"` para o
  mesmo `POST /api/temperaturas` (não sobrescreve t1-t4, pois o backend só atualiza
  chaves presentes no JSON).
- **Wi-Fi**: mesmas credenciais hardcoded que o ESP32 #01 (início do arquivo).
- Não consulta `/api/temperatura-alvo` (só o #01 faz isso).

## Diferenças-chave entre os dois firmwares

| | ESP32 #01 (Placa/Ambiente) | ESP32 #02 (Base/Água) |
|---|---|---|
| Arquivo real | `esp32_painel_status/esp32_painel_status.ino` | `esp32_monitor_ambiente/esp32_monitor_ambiente.ino` |
| Sensores | 3x DS18B20 (ROM fixo) + DHT11 | 2x DS18B20 (por índice) |
| Chaves enviadas | t1-t4, umidade | t5, t6 |
| Limite anti-spike | 10°C | 15°C |
| Consulta temperatura-alvo | Sim (15s) | Não |
| Calibração | Offset fixo em flash | Cruzada (sensor a sensor) + gelo |

## Filtro EMA (pipeline completo, confirmado por leitura da atribuição real, não só comentário)

Idêntico nos dois firmwares — ver nota `[[Filtragem EMA]]` no Knowledge Graph para a
fórmula e a ordem exata (`Raw → Anti-Spike → Calibração → EMA → Final`).

## IP de fallback

`SERVER_HOST` é usado só como valor inicial de `ipServidorAtivo` e como último recurso
depois que a descoberta UDP (`buscarServidorAutomatico()`) e o fallback mDNS falharem —
não é o mecanismo normal de conexão. Ver
[KNOWN_ISSUES.md](KNOWN_ISSUES.md#ip-interno-hardcoded-como-fallback). O valor atual no
código (`10.1.17.239`) é local à rede do laboratório e muda quando a rede muda — não trate
este valor como estável; confirme por Grep (`SERVER_HOST`) antes de citá-lo com confiança.

## Termostato XH-W3002

Citado no código como o controlador físico real do banho — a "temperatura-alvo" do
sistema é só um valor de referência para o ensaio, sem integração de controle com o
XH-W3002 (nem PID nem PWM). Ver [DATA_FLOW.md](DATA_FLOW.md#canal-paralelo-temperatura-alvo-referência-não-controle).
