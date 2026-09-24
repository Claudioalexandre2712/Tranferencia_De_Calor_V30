# Fluxo de Dados: Sensor → Dashboard

> **Atenção (revalidado 2026-09-15):** os nomes de pasta são enganosos — ver
> [HARDWARE_MAP.md](HARDWARE_MAP.md) para a explicação completa. O diagrama abaixo usa o
> arquivo **real** de cada firmware, confirmado pelo campo `doc["device"]` no JSON.

```
DS18B20 x3 (placa) ---\
DHT11 (ambiente)   ----> ESP32 #01 (esp32_painel_status/esp32_painel_status.ino)
                          |
DS18B20 x2 (base/agua) -> ESP32 #02 (esp32_monitor_ambiente/esp32_monitor_ambiente.ino)
```

## Passo a passo

1. **Leitura física** — DS18B20 via OneWire (pino 4, ambos firmwares), DHT11 via pino 27
   (só ESP32 #01).
2. **Filtro no firmware** — ordem real confirmada pela sequência de atribuições no código
   (não pelo comentário isolado):
   - `leituraValida()` — descarta `DEVICE_DISCONNECTED_C`, `85.0`, fora de `[-40,130]°C`,
     ou salto anômalo vs. leitura anterior (>10°C no #01, >15°C no #02).
   - Offset de calibração por sensor, persistido em flash (`Preferences`), ex.
     `OFFSETS_DS18B20[3] = {0.0000, 2.7500, 3.5042}` no #01 — aplicado **antes** do EMA:
     `temperaturasCalibradas[i] = temperaturasRaw[i] + OFFSETS_DS18B20[i]`.
   - Filtro **EMA** (só então): `temperaturasFiltradas[i] = ALPHA_EMA * temperaturasCalibradas[i] + (1 - ALPHA_EMA) * temperaturasFiltradas[i]`,
     `ALPHA_EMA = 0.20f` (mesma constante nos dois firmwares). Ver nota
     `docs/knowledge-graph/Firmware/Filtragem EMA.md` para o pipeline completo.
3. **Descoberta do servidor** — ao iniciar (e após 3 falhas HTTP seguidas), broadcast UDP
   `"TCC_DISCOVER_SERVER"` na porta 5005 → Flask responde `"TCC_SERVER_IP:<porta>"`
   (`_iniciar_auto_discovery_udp`, `app.py:109-143`). Fallback: mDNS, depois IP hardcoded.
4. **Envio HTTP** — a cada 2000ms, `enviarDadosParaServidor()` monta JSON
   (`{"t1":..,"t2":..,"t3":..,"t4":..,"umidade":..,"device":"esp32_01","timestamp":..}`
   no #01, `{"t5":..,"t6":..,"device":"esp32_02",...}` no #02) e faz
   `POST http://<ip>:5000/api/temperaturas`.
5. **Recebimento** — `api_temperaturas` (`app.py:1603`) atualiza só as chaves presentes no
   payload dentro do dict global `monitoring_cache` (`t1..t6`), sob `threading.Lock
   monitoring_lock` — por isso os dois ESP32 não se sobrescrevem mesmo escrevendo
   concorrentemente.
6. **Armazenamento** — só em memória do processo Flask (`monitoring_cache` é um dict
   Python). Sem banco de dados; reiniciar o servidor zera tudo.
7. **Consumo pelo dashboard** — `painel_status.html` faz `fetch('/api/monitoramento')`
   a cada 2000ms (`buscarDadosMonitoramento()`), lê o mesmo `monitoring_cache` (via
   `api_monitoramento`, `app.py:1551`) e também `temperatura_alvo_data`.
8. **Renderização** — JS atualiza cards de KPI (`atualizarKPIs`) e alimenta o array
   `dadosTemperatura` que alimenta o gráfico Plotly.js embutido no dashboard.

## Canal paralelo: temperatura-alvo (referência, não controle)

`POST /api/temperatura-alvo` grava em `temperatura_alvo_data` (dict + lock próprio,
separado de `monitoring_cache`). Faixa válida 0.0–100.0°C, arredondado a 4 casas. O
ESP32 #01 consulta `GET /api/temperatura-alvo` a cada 15s
(função `consultarTemperaturaAlvoServidor()` em
`esp32_painel_status/esp32_painel_status.ino` — arquivo real do ESP32 #01, ver
[HARDWARE_MAP.md](HARDWARE_MAP.md)) só para exibir no serial/diagnóstico — **não existe malha de controle fechado** nem no backend nem no
firmware; é documentado explicitamente no código (`app.py:1680-1685`) como valor de
referência para o ensaio, não um setpoint de PID/PWM do termostato XH-W3002.

## Importação de CSV (não passa pelo backend)

Duas implementações client-side independentes, sem endpoint Flask envolvido:

- `painel_status.html:1683` `carregarArquivoCSV(event)` — popula o histórico do gráfico
  do painel a partir de um CSV exportado (detecta separador `;`/`,`, mapeia colunas por
  nome `hor`/`temp`/`t1..t6`).
- `calculadora_natural.html:651` `carregarCSVNatural(event)` — popula os campos da
  calculadora de convecção natural; `aplicarModoCSV()` (linha 762) escolhe modo de
  agregação (último ponto / todos / últimos 15% = "regime permanente", corte em 85% do
  array).

## Gráficos das calculadoras (fluxo separado, sem sensores)

`visualizacao_plotly.py` gera `grafico_html` (renderizado no servidor) e
`dados_grafico_json` (mesma fonte de dados) a partir do resultado de `calcular_eficiencia`
— usados juntos em `resultado.html`/`resultados_sele.html` para manter gráfico e tabela
sincronizados.
