/*
  =============================================================================
  TCC - BANCADA TÉRMICA EXPERIMENTAL (UFR)
  FIRMWARE: ESP32 #01 - Monitor da Placa e Ambiente
  CANAIS:
    - T1: Início da Placa (DS18B20 #01 - OneWire D4)
    - T2: Centro da Placa (DS18B20 #02 - OneWire D4)
    - T3: Fim da Placa    (DS18B20 #03 - OneWire D4)
    - T4: Ar Ambiente     (DHT11 DATA no pino D27)
  =============================================================================
  RECURSOS IMPLEMENTADOS:
    1. Conversão Assíncrona Não-Bloqueante com período de amostragem REAL fechado
    2. Resolução de 12 bits (passo de 0.0625 °C) -- ver RESOLUCAO_DS18B20
    3. Validação Anti-Spike por TAXA (°C/s) e descarte de conversão obsoleta
    4. Vinculação estrita por ROM Address (sem remapeamento por índice)
    5. Envio orientado a evento: 1 amostra adquirida = 1 amostra transmitida
    6. Menu Serial Interativo:
       - 'G' ou 'g': Calibração em Banho de Gelo (0 °C) -- ÚNICO método válido
       - 'R' ou 'r': Resetar offsets de calibração para 0.00 °C
       - 'S' ou 's': Exibir Status Completo de Diagnóstico
       - 'A' ou 'a': Buscar servidor Flask na rede
  =============================================================================
  REVISÃO METROLÓGICA (auditoria):
    - O comando 'C' (igualar T2/T3 ao T1) foi REMOVIDO. Ele gravava o gradiente
      físico da placa dentro dos offsets, destruindo o dado experimental.
    - Offsets gravados por versões anteriores são invalidados automaticamente
      na primeira inicialização deste firmware (ver CALIB_VERSAO).
  =============================================================================
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Preferences.h>
#include <WiFiUdp.h>

// ── CONFIGURAÇÕES DE REDE E SERVIDOR ─────────────────────────────────────────
#define WIFI_SSID "CLAUDIO 2.4Ghz"
#define WIFI_PASSWORD "enjk8122"

const char* SERVER_HOST = "10.211.228.204"; // IP atual do computador na rede Wi-Fi
const uint16_t SERVER_PORT = 5000;
const char* SERVER_PATH = "/api/temperaturas";
const uint16_t UDP_DISCOVERY_PORT = 5005;

WiFiUDP udpDiscovery;
String ipServidorAtivo = SERVER_HOST;
int falhasConsecutivasHttp = 0;
unsigned long ultimaBuscaServidor = 0;

// ── PINAGEM DO HARDWARE ──────────────────────────────────────────────────────
#define ONE_WIRE_PIN 4      // Barramento OneWire dos DS18B20 da Placa
#define DHT_PIN 27          // Pino de dados do DHT11
#define DHT_TYPE DHT11      // Modelo do sensor de ambiente
#define LED_STATUS_PIN 2    // LED azul onboard do ESP32
#define NUM_SENSORES 3      // T1, T2, T3

// ── ENDEREÇOS ROM CADASTRADOS (DS18B20) ──────────────────────────────────────
const DeviceAddress ENDERECOS_SENSOR[NUM_SENSORES] = {
  {0x28, 0xD8, 0x52, 0xB2, 0x00, 0x00, 0x00, 0xFB}, // T1 - Início
  {0x28, 0x2E, 0x16, 0xB3, 0x00, 0x00, 0x00, 0x42}, // T2 - Meio
  {0x28, 0xD5, 0xE4, 0xB3, 0x00, 0x00, 0x00, 0xED}  // T3 - Fim
};

const char* SENSOR_NAMES[NUM_SENSORES] = {
  "T1_INICIO_PLACA",
  "T2_CENTRO_PLACA",
  "T3_FIM_PLACA"
};

// ── INSTÂNCIAS E VARIÁVEIS GLOBAIS ───────────────────────────────────────────
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);
DHT dht(DHT_PIN, DHT_TYPE);
Preferences preferences;

DeviceAddress enderecosReais[NUM_SENSORES];
float temperaturas[NUM_SENSORES] = {0.0, 0.0, 0.0};
bool sensoresDisponiveis[NUM_SENSORES] = {false, false, false};
bool leiturasValidas[NUM_SENSORES] = {false, false, false};
int errosConsecutivos[NUM_SENSORES] = {0, 0, 0};

float temperaturaAmbiente = 0.0;        // valor publicado (já filtrado)
float temperaturaAmbienteRaw = 0.0;     // leitura direta do DHT11
float umidadeAmbiente = 0.0;
bool temperaturaAmbienteValida = false;
bool emaAmbienteIniciado = false;
unsigned long ultimaAtualizacaoAmbiente = 0;
bool preferencesDisponiveis = false;
bool wifiConectado = false;

// Offsets Metrológicos Padrão (Sem distorção artificial de fábrica)
// - Sensor #01 (índice 0): 0.0000 °C
// - Sensor #02 (índice 1): 0.0000 °C (Offsets ajustados apenas via calibração em ponto fixo)
// - Sensor #03 (índice 2): 0.0000 °C
float OFFSETS_DS18B20[NUM_SENSORES] = {0.0000, 0.0000, 0.0000};

// ── OFFSETS DE REFERÊNCIA (BANHO DE GELO VÁLIDO) ─────────────────────────────
// Resultado de uma calibração em gelo fundente efetivamente realizada, com
// 30/30 amostras válidas por sensor, em 12 bits:
//
//   T1_INICIO_PLACA | Média: -0.2042 °C | Offset: +0.2042 °C
//   T2_CENTRO_PLACA | Média: -0.2979 °C | Offset: +0.2979 °C
//   T3_FIM_PLACA    | Média: -0.2604 °C | Offset: +0.2604 °C
//
// Rastreabilidade: as três médias são exatamente reconstrutíveis como
// (N códigos × 0.0625 °C / 30), com N = -98, -143 e -125 respectivamente,
// o que confirma média real sobre dados quantizados em 12 bits.
// Os três estão dentro da especificação do DS18B20 (±0,5 °C).
//
// Usados como PADRÃO quando a flash não contém calibração (por exemplo após a
// invalidação por CALIB_VERSAO). Uma execução de 'G' sobrescreve estes valores.
//
// ATENÇÃO: só são válidos para ESTES probes nestas posições. Se algum sensor
// for substituído ou trocado de lugar, refaça a calibração com 'G'.
const float OFFSETS_PADRAO_GELO[NUM_SENSORES] = {0.2042f, 0.2979f, 0.2604f};

const float OFFSET_DHT11 = 0.0;
const float TEMPERATURA_REFERENCIA_GELO = 0.0;
const uint8_t NUM_AMOSTRAS_CALIBRACAO = 30;
const uint8_t MIN_AMOSTRAS_CALIBRACAO = 24;

// Validação da calibração em gelo: só aceita amostras plausíveis de gelo fundente
// e só grava o offset se a média ficar realmente próxima de 0 °C.
const float JANELA_AMOSTRA_GELO = 5.0f;   // °C: descarta amostra fora de -5..+5 (sensor fora do banho)
const float MAX_MEDIA_GELO      = 2.0f;   // °C: média |T| acima disto => banho inválido, aborta
const float MAX_OFFSET_ACEITO   = 1.5f;   // °C: offset acima disto => sensor provavelmente falsificado

// Invalida automaticamente offsets gravados por firmwares anteriores.
// Incremente este valor sempre que a semântica do offset mudar.
const uint32_t CALIB_VERSAO = 2;

// ── RESOLUÇÃO DOS DS18B20 ────────────────────────────────────────────────────
// 12 bits = 0.0625 °C / 750 ms   <-- escolhido: o gradiente da placa é da ordem
// 11 bits = 0.1250 °C / 375 ms       de 1 °C, e 0.25 °C (10 bits) representaria
// 10 bits = 0.2500 °C / 188 ms       25% do sinal de interesse.
//  9 bits = 0.5000 °C /  94 ms
const uint8_t  RESOLUCAO_DS18B20  = 12;
const unsigned long TEMPO_CONVERSAO = 750;  // ms; DEVE casar com RESOLUCAO_DS18B20

// ── RASTREABILIDADE METROLÓGICA E FILTRO DIGITAL EMA ─────────────────────────
// Cadeia metrológica:
// 1. Leitura Física (Raw) -> 2. Validação Anti-Spike -> 3. Calibração (Offset) -> 4. EMA -> 5. Valor Filtrado Final
float temperaturasRaw[NUM_SENSORES] = {0.0, 0.0, 0.0};        // Leitura física direta do DS18B20 (sem offset e sem filtro)
float temperaturasCalibradas[NUM_SENSORES] = {0.0, 0.0, 0.0}; // Dado experimental com offset de calibração preservado
float temperaturasFiltradas[NUM_SENSORES] = {0.0, 0.0, 0.0};  // Valor suavizado pelo filtro EMA
bool emaIniciado[NUM_SENSORES] = {false, false, false};        // Flag individual de inicialização do estado do EMA
unsigned long ultimaAtualizacaoValida[NUM_SENSORES] = {0, 0, 0}; // millis da última leitura válida de cada canal

// ── TEMPORIZAÇÃO NÃO-BLOQUEANTE ──────────────────────────────────────────────
// INTERVALO_LEITURA é medido entre REQUISIÇÕES de conversão (e não entre leituras),
// portanto é o período de amostragem REAL. Precisa ser > TEMPO_CONVERSAO.
const unsigned long INTERVALO_LEITURA = 1000;
const unsigned long INTERVALO_RESCAN = 6000;
const unsigned long INTERVALO_DHT11 = 2500;  // ms (DHT11 requer mínimo 2.0s entre leituras)

// Conversão cuja leitura atrasou além disto (bloqueio de rede, rescan) é
// DESCARTADA em vez de ser lida como se fosse do instante atual.
const unsigned long IDADE_MAXIMA_CONVERSAO = 1500;  // ms

// Dado mais velho que isto não é transmitido: evita publicar valor congelado.
const unsigned long IDADE_MAXIMA_DADO = 5000;       // ms

// Filtro EMA: alpha derivado do período de amostragem REAL, para que a constante
// de tempo declarada (TAU_EMA_S) seja a que efetivamente ocorre no ensaio.
//   alpha = Δt / (tau + Δt);  com Δt = 1.0 s e tau = 4.0 s  ->  alpha = 0.20
const float TAU_EMA_S = 4.0f;
const float DT_EMA_S  = INTERVALO_LEITURA / 1000.0f;
const float ALPHA_EMA = DT_EMA_S / (TAU_EMA_S + DT_EMA_S);

// O DHT11 amostra a 2.5 s, então precisa do seu próprio alpha para resultar na
// MESMA constante de tempo TAU_EMA_S dos DS18B20 (senão T4 e T1..T3 teriam
// dinâmicas diferentes e o ΔT placa-ambiente ficaria errado em transiente).
const float DT_EMA_DHT_S = INTERVALO_DHT11 / 1000.0f;
const float ALPHA_EMA_DHT = DT_EMA_DHT_S / (TAU_EMA_S + DT_EMA_DHT_S);

// Anti-spike expresso como TAXA, para não depender do período de amostragem.
const float MAX_TAXA_C_POR_S = 10.0f;

unsigned long ultimaRequisicaoConversao = 0;
bool conversaoEmAndamento = false;
unsigned long ultimaLeituraDHT = 0;
unsigned long ultimoRescan = 0;
unsigned long ledApagarTimestamp = 0;
bool ledAceso = false;

// Envio orientado a evento: marcado a cada nova amostra adquirida.
bool novaAmostraDisponivel = false;
unsigned long instanteAmostra = 0;

// ── CONFIGURAÇÃO DE TEMPERATURA-ALVO DO ENSAIO (REFERÊNCIA NÃO-MEDIDA) ───────
// A temperatura-alvo atua estritamente como valor de REFERÊNCIA do ensaio;
// NÃO é uma temperatura medida, NÃO substitui leituras dos sensores físicos e
// NÃO implementa controle PID/PWM ou chaveamento do aquecedor (XH-W3002 permanece no controle físico).
float temperaturaAlvo = 0.0;
bool temperaturaAlvoConfigurada = false;
unsigned long ultimoQueryTemperaturaAlvo = 0;
const unsigned long INTERVALO_CONSULTA_ALVO = 15000; // 15s (frequência desacoplada da leitura rápida)
const char* PATH_TEMPERATURA_ALVO = "/api/temperatura-alvo";

// ── FUNÇÕES AUXILIARES DE LED ────────────────────────────────────────────────
void piscarLed(int vezes, int tempoMs) {
  for (int i = 0; i < vezes; i++) {
    digitalWrite(LED_STATUS_PIN, HIGH);
    delay(tempoMs);
    digitalWrite(LED_STATUS_PIN, LOW);
    if (i + 1 < vezes) delay(tempoMs);
  }
}

void acionarLedPulso() {
  digitalWrite(LED_STATUS_PIN, HIGH);
  ledApagarTimestamp = millis();
  ledAceso = true;
}

void atualizarLedStatus() {
  // Subtração de unsigned long: imune ao overflow de millis() em 49,7 dias.
  if (ledAceso && (millis() - ledApagarTimestamp >= 100)) {
    digitalWrite(LED_STATUS_PIN, LOW);
    ledAceso = false;
  }
}

// ── FUNÇÃO: IMPRIMIR ENDEREÇO HEX ────────────────────────────────────────────
void imprimirEndereco(const DeviceAddress endereco) {
  for (uint8_t i = 0; i < 8; i++) {
    if (endereco[i] < 16) Serial.print("0");
    Serial.print(endereco[i], HEX);
  }
}

// ── FUNÇÃO: CONECTAR WIFI ────────────────────────────────────────────────────
void conectarWiFi() {
  Serial.print("\n[WIFI] Conectando a ");
  Serial.println(WIFI_SSID);

  WiFi.disconnect(true);
  delay(100);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  if (strlen(WIFI_PASSWORD) > 0) {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  } else {
    WiFi.begin(WIFI_SSID);
  }

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 25) {
    delay(400);
    digitalWrite(LED_STATUS_PIN, !digitalRead(LED_STATUS_PIN));
    Serial.print(".");
    tentativas++;
  }

  // Fallback inteligente: se havia senha configurada mas falhou, tenta conectar em modo aberto
  if (WiFi.status() != WL_CONNECTED && strlen(WIFI_PASSWORD) > 0) {
    Serial.println("\n[WIFI] Tentando conexão em modo aberto (sem senha)...");
    WiFi.disconnect();
    delay(200);
    WiFi.begin(WIFI_SSID);
    tentativas = 0;
    while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
      delay(400);
      digitalWrite(LED_STATUS_PIN, !digitalRead(LED_STATUS_PIN));
      Serial.print(".");
      tentativas++;
    }
  }

  digitalWrite(LED_STATUS_PIN, LOW);
  Serial.println();

  wifiConectado = (WiFi.status() == WL_CONNECTED);
  if (wifiConectado) {
    Serial.println("[WIFI] ✓ Conectado com sucesso!");
    Serial.print("[WIFI] IP do ESP32: ");
    Serial.println(WiFi.localIP());
    Serial.print("[WIFI] RSSI: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    piscarLed(2, 80);
  } else {
    Serial.println("[WIFI] ✗ Falha na conexão Wi-Fi. Verifique SSID/Senha.");
  }
}

// ── FUNÇÃO: DESCOBERTA AUTOMÁTICA DO SERVIDOR FLASK NA REDE ─────────────────
void buscarServidorAutomatico() {
  if (WiFi.status() != WL_CONNECTED) return;

  Serial.println("\n[AUTO-DISCOVERY] Procurando servidor Flask na rede...");

  // 1ª Tentativa: UDP Broadcast (Global e Sub-rede local)
  udpDiscovery.begin(0);
  IPAddress broadcastGlobal(255, 255, 255, 255);
  IPAddress broadcastSubnet = WiFi.broadcastIP();

  udpDiscovery.beginPacket(broadcastGlobal, UDP_DISCOVERY_PORT);
  udpDiscovery.write((const uint8_t*)"TCC_DISCOVER_SERVER", 19);
  udpDiscovery.endPacket();

  if (broadcastSubnet != broadcastGlobal && broadcastSubnet != IPAddress(0, 0, 0, 0) && broadcastSubnet[0] != 0) {
    udpDiscovery.beginPacket(broadcastSubnet, UDP_DISCOVERY_PORT);
    udpDiscovery.write((const uint8_t*)"TCC_DISCOVER_SERVER", 19);
    udpDiscovery.endPacket();
  }

  unsigned long inicio = millis();
  while (millis() - inicio < 1500) {
    int packetSize = udpDiscovery.parsePacket();
    if (packetSize > 0) {
      char reply[64] = {0};
      udpDiscovery.read(reply, sizeof(reply) - 1);
      if (strstr(reply, "TCC_SERVER_IP") != NULL) {
        IPAddress respIp = udpDiscovery.remoteIP();
        if (respIp != IPAddress(0, 0, 0, 0) && respIp[0] != 0) {
          ipServidorAtivo = respIp.toString();
          Serial.printf("[AUTO-DISCOVERY] ✓ Servidor Flask localizado via Broadcast UDP: %s:%d\n\n", 
                        ipServidorAtivo.c_str(), SERVER_PORT);
          udpDiscovery.stop();
          falhasConsecutivasHttp = 0;
          return;
        }
      }
    }
    delay(25);
  }
  udpDiscovery.stop();

  // 2ª Tentativa: Hostname do Computador via mDNS / DNS (rejeitando 0.0.0.0 de DNS de rede aberta)
  IPAddress hostIp;
  if ((WiFi.hostByName("GalaxyBook4Pro.local", hostIp) && hostIp != IPAddress(0, 0, 0, 0) && hostIp[0] != 0) || 
      (WiFi.hostByName("GalaxyBook4Pro", hostIp) && hostIp != IPAddress(0, 0, 0, 0) && hostIp[0] != 0)) {
    ipServidorAtivo = hostIp.toString();
    Serial.printf("[AUTO-DISCOVERY] ✓ Servidor localizado via Hostname/mDNS: %s:%d\n\n", 
                  ipServidorAtivo.c_str(), SERVER_PORT);
    falhasConsecutivasHttp = 0;
    return;
  }

  // 3ª Tentativa: Fallback para o IP configurado do computador na rede
  ipServidorAtivo = SERVER_HOST;
  Serial.printf("[AUTO-DISCOVERY] Usando IP de fallback configurado: %s:%d\n\n", 
                ipServidorAtivo.c_str(), SERVER_PORT);
}

// ── FUNÇÃO: DESCOBRIR SENSORES DS18B20 ───────────────────────────────────────
void descobrirSensores() {
  sensors.begin();
  delay(100);
  int quantidade = sensors.getDeviceCount();

  Serial.println("\n╔════════════════════════════════════════════════════════════╗");
  Serial.println("║            BUSCA DE SENSORES DS18B20 (GPIO 4)              ║");
  Serial.println("╚════════════════════════════════════════════════════════════╝");
  Serial.printf("  Sensores físicos encontrados no barramento: %d\n", quantidade);

  // Vinculação ESTRITA por ROM Address.
  // NUNCA remapear por índice do barramento: a ordem de descoberta do OneWire não
  // é uma propriedade física do sensor, e um remapeamento faria o sensor do fim da
  // placa ser publicado como se fosse o do centro.
  for (int i = 0; i < NUM_SENSORES; i++) {
    if (sensors.isConnected(ENDERECOS_SENSOR[i])) {
      memcpy(enderecosReais[i], ENDERECOS_SENSOR[i], sizeof(DeviceAddress));
      sensoresDisponiveis[i] = true;
      errosConsecutivos[i] = 0;
      Serial.printf("  ✓ %s -> Vinculado ao ROM cadastrado: ", SENSOR_NAMES[i]);
      imprimirEndereco(enderecosReais[i]);
      Serial.println();
    } else {
      sensoresDisponiveis[i] = false;
      Serial.printf("  ✗ %s -> ROM cadastrado NÃO responde: ", SENSOR_NAMES[i]);
      imprimirEndereco(ENDERECOS_SENSOR[i]);
      Serial.println();
    }
    leiturasValidas[i] = false;
  }

  // Lista ROMs presentes que não estão cadastrados (ajuda a cadastrar sensor novo)
  if (quantidade > 0) {
    DeviceAddress achado;
    for (int b = 0; b < quantidade; b++) {
      if (!sensors.getAddress(achado, b)) continue;
      bool cadastrado = false;
      for (int i = 0; i < NUM_SENSORES; i++) {
        if (memcmp(achado, ENDERECOS_SENSOR[i], sizeof(DeviceAddress)) == 0) { cadastrado = true; break; }
      }
      if (!cadastrado) {
        Serial.print("  [AVISO] ROM presente no barramento mas NÃO cadastrado: ");
        imprimirEndereco(achado);
        Serial.println("  <- adicione em ENDERECOS_SENSOR[] se for um probe novo");
      }
    }
  }

  sensors.setResolution(RESOLUCAO_DS18B20);
  sensors.setWaitForConversion(false);
  conversaoEmAndamento = false;  // descarta conversão órfã iniciada antes do rescan
  // Passo do DS18B20 = 2^-(R-8): 12b->0.0625  11b->0.125  10b->0.25  9b->0.5
  Serial.printf("  Resolução: %u bits (passo %.4f °C, conversão %lu ms)\n",
                RESOLUCAO_DS18B20, 1.0f / (1 << (RESOLUCAO_DS18B20 - 8)), TEMPO_CONVERSAO);
  Serial.println("------------------------------------------------------------\n");
}

// ── FUNÇÃO: VALIDAÇÃO METROLÓGICA E ANTI-SPIKE ──────────────────────────────
bool leituraValida(float leituraBruta, float leituraAnterior, bool temAnteriorValida, unsigned long dtMs) {
  if (isnan(leituraBruta) || leituraBruta == DEVICE_DISCONNECTED_C || leituraBruta == 85.0 ||
      leituraBruta < -40.0 || leituraBruta > 130.0) {
    return false;
  }
  // Anti-Spike por TAXA: o limite acompanha o intervalo real entre amostras,
  // em vez de assumir um Δt fixo que pode não corresponder ao ciclo executado.
  if (temAnteriorValida && dtMs > 0) {
    float limite = MAX_TAXA_C_POR_S * (dtMs / 1000.0f);
    if (limite < 1.0f) limite = 1.0f;   // piso: nunca rejeitar variação fisicamente plausível
    if (fabsf(leituraBruta - leituraAnterior) > limite) {
      Serial.printf("  [FILTRO] Salto de %.3f °C em %lu ms descartado (limite %.2f °C)\n",
                    fabsf(leituraBruta - leituraAnterior), dtMs, limite);
      return false;
    }
  }
  return true;
}

// ── FUNÇÃO: DISPARAR E LER TEMPERATURAS (ASSÍNCRONO + FILTRO EMA CONSERVADOR) ──
void processarLeiturasAssincronas() {
  unsigned long agora = millis();

  // Fase 0: Descartar conversão obsoleta.
  // Se a leitura atrasou muito (bloqueio de rede, rescan), o scratchpad contém o
  // resultado de uma conversão antiga. Lê-lo agora produziria uma amostra velha
  // rotulada como se fosse do instante atual.
  if (conversaoEmAndamento && (agora - ultimaRequisicaoConversao > IDADE_MAXIMA_CONVERSAO)) {
    Serial.printf("  [TEMPO] Conversão obsoleta (%lu ms) descartada.\n",
                  agora - ultimaRequisicaoConversao);
    conversaoEmAndamento = false;
  }

  // Fase 1: Disparar requisição de conversão não-bloqueante.
  // O período é medido entre REQUISIÇÕES, portanto INTERVALO_LEITURA é o período
  // de amostragem REAL (e não INTERVALO_LEITURA + TEMPO_CONVERSAO).
  if (!conversaoEmAndamento && (agora - ultimaRequisicaoConversao >= INTERVALO_LEITURA)) {
    sensors.requestTemperatures();
    ultimaRequisicaoConversao = agora;
    conversaoEmAndamento = true;
    return;
  }

  // Fase 2: Coletar leituras quando a conversão tiver terminado
  if (conversaoEmAndamento && (agora - ultimaRequisicaoConversao >= TEMPO_CONVERSAO)) {
    conversaoEmAndamento = false;
    instanteAmostra = ultimaRequisicaoConversao;  // instante físico da medida
    novaAmostraDisponivel = true;

    // Coleta, validação metrológica, calibração e filtragem EMA dos 3 DS18B20
    for (int i = 0; i < NUM_SENSORES; i++) {
      if (!sensoresDisponiveis[i]) continue;

      // 1. Leitura Física Direta do DS18B20, SEMPRE pelo ROM Address.
      // Sem fallback por índice: em caso de falha de CRC o índice do barramento
      // poderia devolver a temperatura de OUTRO sensor físico.
      float leituraFisica = sensors.getTempC(enderecosReais[i]);

      unsigned long dt = (ultimaAtualizacaoValida[i] > 0)
                       ? (agora - ultimaAtualizacaoValida[i]) : INTERVALO_LEITURA;

      // 2. Validação Metrológica e Rejeição de Anomalias/Spikes
      if (leituraValida(leituraFisica, temperaturasRaw[i], emaIniciado[i], dt)) {
        // Armazena a leitura física pura validada
        temperaturasRaw[i] = leituraFisica;

        // 3. Aplicação do Offset de Calibração (Dado Experimental Preservado)
        temperaturasCalibradas[i] = temperaturasRaw[i] + OFFSETS_DS18B20[i];

        // 4. Filtro EMA. Primeira leitura válida: Tf = T (não inicializa com zero)
        if (!emaIniciado[i]) {
          temperaturasFiltradas[i] = temperaturasCalibradas[i];
          emaIniciado[i] = true;
        } else {
          // Tf(n) = alpha * T(n) + (1 - alpha) * Tf(n-1)
          temperaturasFiltradas[i] = (ALPHA_EMA * temperaturasCalibradas[i]) +
                                     ((1.0f - ALPHA_EMA) * temperaturasFiltradas[i]);
        }

        // 5. Valor Final atribuído para exibição e telemetria
        temperaturas[i] = temperaturasFiltradas[i];
        leiturasValidas[i] = true;
        ultimaAtualizacaoValida[i] = agora;
        errosConsecutivos[i] = 0;
      } else {
        // Leitura inválida: NÃO atualiza o EMA e NÃO substitui o último valor válido.
        errosConsecutivos[i]++;
        // Tolera falhas isoladas de CRC, mas invalida o canal rapidamente para que
        // nenhum valor congelado continue sendo publicado como se fosse atual.
        if (errosConsecutivos[i] >= 3) {
          leiturasValidas[i] = false;
        }
        if (errosConsecutivos[i] >= 10) {
          sensoresDisponiveis[i] = false; // Força rescan
          emaIniciado[i] = false;         // Reinicializa sem degrau na reconexão
          Serial.printf("  [SENSOR] %s perdido no barramento. Rescan agendado.\n", SENSOR_NAMES[i]);
        }
      }
    }
  }
}

// ── FUNÇÃO: LEITURA NÃO-BLOQUEANTE DO SENSOR DHT11 (AMBIENTE) ───────────────
void processarLeituraDHT11() {
  unsigned long agora = millis();
  if (agora - ultimaLeituraDHT >= INTERVALO_DHT11) {
    ultimaLeituraDHT = agora;

    float tDht = dht.readTemperature();
    float uDht = dht.readHumidity();

    // Sem retentativa bloqueante: uma leitura falha simplesmente não atualiza o
    // canal, e a próxima tentativa ocorre no ciclo seguinte (2.5 s depois).
    if (!isnan(tDht) && tDht > -20.0 && tDht < 70.0) {
      temperaturaAmbienteRaw = tDht + OFFSET_DHT11;

      // Mesmo EMA dos DS18B20: sem isto o T4 responderia instantaneamente
      // enquanto T1/T2/T3 carregam a constante de tempo do filtro, tornando
      // errado qualquer ΔT placa-ambiente calculado durante transiente.
      if (!emaAmbienteIniciado) {
        temperaturaAmbiente = temperaturaAmbienteRaw;
        emaAmbienteIniciado = true;
      } else {
        temperaturaAmbiente = (ALPHA_EMA_DHT * temperaturaAmbienteRaw) +
                              ((1.0f - ALPHA_EMA_DHT) * temperaturaAmbiente);
      }
      temperaturaAmbienteValida = true;
      ultimaAtualizacaoAmbiente = agora;
    }

    if (!isnan(uDht) && uDht >= 0.0 && uDht <= 100.0) {
      umidadeAmbiente = uDht;
    }
  }

  // Invalida o canal se o DHT11 parar de responder, em vez de publicar o
  // último valor indefinidamente.
  if (temperaturaAmbienteValida && (agora - ultimaAtualizacaoAmbiente > 4 * INTERVALO_DHT11)) {
    temperaturaAmbienteValida = false;
    emaAmbienteIniciado = false;
    Serial.println("  [DHT11] Sem resposta. Canal T4 invalidado.");
  }
}

// ── FUNÇÃO: CARREGAR OFFSETS DA FLASH (PREFERENCES) ──────────────────────────
void carregarOffsetsCalibracao() {
  preferencesDisponiveis = preferences.begin("calibracao", false);
  if (!preferencesDisponiveis) {
    Serial.println("[PREF] Falha ao acessar memoria flash; usando offsets padrao de bancada.");
    return;
  }
  // Offsets gravados por firmwares anteriores são DESCARTADOS.
  // Motivo: o comando 'C' (removido) gravava "raw_T1 - raw_Ti", ou seja, o
  // gradiente físico da placa, dentro do offset de calibração. Reaproveitar
  // esses valores contaminaria permanentemente todos os ensaios.
  uint32_t versaoGravada = preferences.getUInt("ver", 0);
  if (versaoGravada != CALIB_VERSAO) {
    Serial.println("\n  ╔══════════════════════════════════════════════════════════╗");
    Serial.println("  ║  [PREF] CALIBRAÇÃO ANTIGA DETECTADA E DESCARTADA         ║");
    Serial.println("  ║  Offsets zerados. Refaça a calibração com 'G'            ║");
    Serial.println("  ║  (banho de gelo fundente, TODOS os probes imersos).      ║");
    Serial.println("  ╚══════════════════════════════════════════════════════════╝");
    Serial.printf("  Valores descartados: T1=%+.4f  T2=%+.4f  T3=%+.4f\n",
                  preferences.getFloat("t1", 0.0f),
                  preferences.getFloat("t2", 0.0f),
                  preferences.getFloat("t3", 0.0f));

    // Restaura os offsets do banho de gelo documentado em OFFSETS_PADRAO_GELO,
    // em vez de zerar: são uma calibração de ponto fixo real e verificada.
    Serial.println("  Restaurando offsets do banho de gelo de referência:");
    for (int i = 0; i < NUM_SENSORES; i++) {
      OFFSETS_DS18B20[i] = OFFSETS_PADRAO_GELO[i];
      Serial.printf("       %-16s %+.4f °C\n", SENSOR_NAMES[i], OFFSETS_DS18B20[i]);
    }
    Serial.println("  Confirme com 'G' se algum probe foi trocado de posição.");

    preferences.putFloat("t1", OFFSETS_DS18B20[0]);
    preferences.putFloat("t2", OFFSETS_DS18B20[1]);
    preferences.putFloat("t3", OFFSETS_DS18B20[2]);
    preferences.putUInt("ver", CALIB_VERSAO);
    return;
  }

  OFFSETS_DS18B20[0] = preferences.getFloat("t1", 0.0000);
  OFFSETS_DS18B20[1] = preferences.getFloat("t2", 0.0000);
  OFFSETS_DS18B20[2] = preferences.getFloat("t3", 0.0000);

  Serial.println("[PREF] Offsets de calibração T1/T2/T3 carregados:");
  for (int i = 0; i < NUM_SENSORES; i++) {
    Serial.printf("       %-16s %+.4f °C%s\n", SENSOR_NAMES[i], OFFSETS_DS18B20[i],
                  (fabsf(OFFSETS_DS18B20[i]) > MAX_OFFSET_ACEITO) ? "   <-- SUSPEITO!" : "");
  }
}

// ── FUNÇÃO: CALIBRAÇÃO EM BANHO DE GELO (0 °C) ──────────────────────────────
void calibrarSensoresGelo() {
  float somas[NUM_SENSORES] = {0.0, 0.0, 0.0};
  uint8_t amostrasValidas[NUM_SENSORES] = {0, 0, 0};
  uint8_t amostrasForaDoGelo[NUM_SENSORES] = {0, 0, 0};
  float novosOffsets[NUM_SENSORES];

  for (uint8_t i = 0; i < NUM_SENSORES; i++) {
    novosOffsets[i] = OFFSETS_DS18B20[i];
  }

  Serial.println("\n╔════════════════════════════════════════════════════╗");
  Serial.println("║       CALIBRAÇÃO POR BANHO DE GELO (0.00 °C)       ║");
  Serial.println("║ T1, T2 e T3 DEVEM estar imersos no gelo fundente.  ║");
  Serial.println("║ Coletando 30 amostras...                           ║");
  Serial.println("╚════════════════════════════════════════════════════╝");

  sensors.setWaitForConversion(true);
  for (uint8_t amostra = 0; amostra < NUM_AMOSTRAS_CALIBRACAO; amostra++) {
    sensors.requestTemperatures();
    digitalWrite(LED_STATUS_PIN, !digitalRead(LED_STATUS_PIN));
    Serial.printf("Amostra %u/%u  ", amostra + 1, NUM_AMOSTRAS_CALIBRACAO);

    for (uint8_t i = 0; i < NUM_SENSORES; i++) {
      if (!sensoresDisponiveis[i]) continue;
      float bruta = sensors.getTempC(enderecosReais[i]);
      if (bruta == DEVICE_DISCONNECTED_C || bruta == 85.0 || isnan(bruta)) continue;

      Serial.printf("| %s=%.3f ", SENSOR_NAMES[i], bruta);

      // Só aceita amostra compatível com gelo fundente. Um probe esquecido fora
      // do banho, a 25 °C, produziria um offset de -25 °C gravado na flash.
      if (fabsf(bruta - TEMPERATURA_REFERENCIA_GELO) <= JANELA_AMOSTRA_GELO) {
        somas[i] += bruta;
        amostrasValidas[i]++;
      } else {
        amostrasForaDoGelo[i]++;
      }
    }
    Serial.println();
    delay(950);
  }
  digitalWrite(LED_STATUS_PIN, LOW);
  sensors.setWaitForConversion(false);
  conversaoEmAndamento = false;

  bool algumOffsetSalvo = false;
  Serial.println("\n--- RESULTADOS DA CALIBRAÇÃO ---");
  for (uint8_t i = 0; i < NUM_SENSORES; i++) {
    Serial.printf("%-16s | Válidas: %2u | Fora do gelo: %2u ",
                  SENSOR_NAMES[i], amostrasValidas[i], amostrasForaDoGelo[i]);

    if (amostrasValidas[i] < MIN_AMOSTRAS_CALIBRACAO) {
      Serial.printf("| [ABORTADO: só %u de %u amostras válidas. O probe está no gelo?]\n",
                    amostrasValidas[i], MIN_AMOSTRAS_CALIBRACAO);
      continue;
    }

    float media = somas[i] / amostrasValidas[i];
    float offsetCandidato = TEMPERATURA_REFERENCIA_GELO - media;

    if (fabsf(media) > MAX_MEDIA_GELO) {
      Serial.printf("| Média: %.4f °C | [ABORTADO: longe demais de 0 °C. Banho inválido.]\n", media);
      continue;
    }
    if (fabsf(offsetCandidato) > MAX_OFFSET_ACEITO) {
      Serial.printf("| Média: %.4f °C | [ABORTADO: offset %+.4f °C excede %.2f °C.\n",
                    media, offsetCandidato, MAX_OFFSET_ACEITO);
      Serial.println("                     O DS18B20 está fora da especificação (±0,5 °C).");
      Serial.println("                     Sensor provavelmente falsificado: substitua o probe.]");
      continue;
    }

    novosOffsets[i] = offsetCandidato;
    OFFSETS_DS18B20[i] = offsetCandidato;
    Serial.printf("| Média: %.4f °C | Novo Offset: %+.4f °C [OK]\n", media, offsetCandidato);
    algumOffsetSalvo = true;
  }

  if (algumOffsetSalvo && preferencesDisponiveis) {
    preferences.putFloat("t1", novosOffsets[0]);
    preferences.putFloat("t2", novosOffsets[1]);
    preferences.putFloat("t3", novosOffsets[2]);
    preferences.putUInt("ver", CALIB_VERSAO);
    Serial.println("✓ OFFSETS GRAVADOS NA MEMÓRIA FLASH.");
    piscarLed(3, 100);
  } else {
    Serial.println("✗ NENHUM offset gravado. Os valores anteriores foram mantidos.");
  }
  Serial.println("--------------------------------\n");
}

// ── FUNÇÃO: RESETAR OFFSETS DE CALIBRAÇÃO ───────────────────────────────────
void zerarOffsetsCalibracao() {
  OFFSETS_DS18B20[0] = 0.0;
  OFFSETS_DS18B20[1] = 0.0;
  OFFSETS_DS18B20[2] = 0.0;

  if (preferencesDisponiveis) {
    preferences.putFloat("t1", 0.0);
    preferences.putFloat("t2", 0.0);
    preferences.putFloat("t3", 0.0);
    preferences.putUInt("ver", CALIB_VERSAO);
    Serial.println("[PREF] ✓ Offsets T1/T2/T3 zerados (0.00 °C) na memória flash.");
    piscarLed(2, 150);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// REMOVIDO: calibrarSensoresComSensor1() -- antigo comando 'C'
//
// A função calculava  OFFSET[i] = raw_T1 - raw_Ti  e gravava na flash, forçando
// T2 e T3 a lerem exatamente T1. Numa placa com gradiente térmico real isso
// converte o PRÓPRIO FENÔMENO MEDIDO em um viés constante de calibração,
// apagando o gradiente de todos os ensaios seguintes de forma persistente.
//
// Sintoma diagnóstico da versão anterior (offsets múltiplos exatos do LSB, com
// o sensor de referência em exatamente +0.0000 °C):
//     T1 = +0.0000   T2 = -1.1875 (=19 LSB)   T3 = -0.8125 (=13 LSB)
//
// O único método de calibração metrologicamente válido aqui é o ponto fixo
// (banho de gelo fundente), implementado em calibrarSensoresGelo() -- comando 'G'.
// ─────────────────────────────────────────────────────────────────────────────

// ── FUNÇÃO: EXIBIR STATUS COMPLETO NO MONITOR SERIAL ────────────────────────
void exibirStatusCompleto() {
  Serial.println("\n╔════════════════════════════════════════════════════════════╗");
  Serial.println("║          DIAGNÓSTICO DO ESP32 #01 (PLACA & AMBIENTE)       ║");
  Serial.println("╚════════════════════════════════════════════════════════════╝");
  Serial.print("Wi-Fi: ");
  Serial.println(wifiConectado ? "✓ Conectado" : "✗ Desconectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Sinal RSSI: ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  Serial.print("Servidor Alvo: http://");
  Serial.print(ipServidorAtivo);
  Serial.print(":");
  Serial.print(SERVER_PORT);
  Serial.println(SERVER_PATH);
  Serial.println("\n--- LEITURAS DOS SENSORES (RASTREAMENTO METROLÓGICO) ---");

  unsigned long agora = millis();
  for (int i = 0; i < NUM_SENSORES; i++) {
    Serial.printf("  %-16s: ", SENSOR_NAMES[i]);
    bool fresco = leiturasValidas[i] && (agora - ultimaAtualizacaoValida[i] <= IDADE_MAXIMA_DADO);
    if (fresco) {
      Serial.printf("FINAL (EMA) = %.4f °C  [Raw = %.4f °C | Offset = %+.4f °C | Calibrado = %.4f °C | idade %lu ms]%s\n",
                    temperaturasFiltradas[i], temperaturasRaw[i], OFFSETS_DS18B20[i],
                    temperaturasCalibradas[i], agora - ultimaAtualizacaoValida[i],
                    (fabsf(OFFSETS_DS18B20[i]) > MAX_OFFSET_ACEITO) ? "  <-- OFFSET SUSPEITO" : "");
    } else if (leiturasValidas[i]) {
      Serial.printf("DADO OBSOLETO (última leitura válida há %lu ms) - NÃO transmitido\n",
                    agora - ultimaAtualizacaoValida[i]);
    } else {
      Serial.printf("ERRO / Desconectado (%d erros consecutivos) - NÃO transmitido\n", errosConsecutivos[i]);
    }
  }

  Serial.print("  T4_AMBIENTE (DHT11): ");
  if (temperaturaAmbienteValida) {
    Serial.printf("FINAL (EMA) = %.2f °C  [Raw = %.2f °C] | Umidade: %.1f %%\n",
                  temperaturaAmbiente, temperaturaAmbienteRaw, umidadeAmbiente);
  } else {
    Serial.println("ERRO / DHT11 Sem Leitura - NÃO transmitido");
  }

  Serial.printf("\n  Aquisição: %lu ms | Conversão: %lu ms | Resolução: %u bits (passo %.4f °C)\n",
                INTERVALO_LEITURA, TEMPO_CONVERSAO, RESOLUCAO_DS18B20,
                1.0f / (1 << (RESOLUCAO_DS18B20 - 8)));
  Serial.printf("  EMA: alpha = %.4f -> tau = %.2f s | DHT11 alpha = %.4f\n",
                ALPHA_EMA, TAU_EMA_S, ALPHA_EMA_DHT);

  Serial.print("  TEMPERATURA-ALVO (REFERÊNCIA): ");
  if (temperaturaAlvoConfigurada) {
    Serial.printf("%.2f °C [Configurada no Painel]\n", temperaturaAlvo);
  } else {
    Serial.println("Não configurada");
  }

  Serial.print("Memória RAM Livre: ");
  Serial.print(esp_get_free_heap_size());
  Serial.println(" bytes");
  Serial.println("============================================================\n");
}

// ── FUNÇÃO: ENVIAR DADOS VIA HTTP POST PARA O FLASK ─────────────────────────
void enviarDadosParaServidor() {
  // NÃO chama conectarWiFi() aqui: aquela função bloqueia até ~18 s, congelando
  // toda a aquisição. A reconexão é tratada de forma não-bloqueante em manterWiFi().
  if (!wifiConectado) return;

  unsigned long agora = millis();
  String url = "http://" + ipServidorAtivo + ":" + String(SERVER_PORT) + SERVER_PATH;
  StaticJsonDocument<320> doc;

  // Um canal só é transmitido se a leitura for VÁLIDA e RECENTE.
  // A condição antiga ("|| temperaturas[i] > 0.0") republicava indefinidamente o
  // último valor de um sensor morto, sem qualquer sinalização de erro.
  const char* chaves[NUM_SENSORES] = {"t1", "t2", "t3"};
  for (int i = 0; i < NUM_SENSORES; i++) {
    if (leiturasValidas[i] && (agora - ultimaAtualizacaoValida[i] <= IDADE_MAXIMA_DADO)) {
      doc[chaves[i]] = round(temperaturas[i] * 10000) / 10000.0;
    }
  }
  if (temperaturaAmbienteValida && (agora - ultimaAtualizacaoAmbiente <= 4 * INTERVALO_DHT11)) {
    doc["t4"] = round(temperaturaAmbiente * 10000) / 10000.0;
    if (umidadeAmbiente > 0.0) doc["umidade"] = round(umidadeAmbiente * 10) / 10.0;
  }
  doc["device"] = "esp32_01";
  doc["timestamp"] = millis();
  doc["amostra_ms"] = instanteAmostra;          // instante físico da conversão
  doc["idade_ms"] = agora - instanteAmostra;    // permite detectar dado atrasado

  String payload;
  serializeJson(doc, payload);

  WiFiClient client;
  HTTPClient http;
  if (!http.begin(client, url)) {
    Serial.println("[HTTP] Falha ao iniciar conexão HTTP.");
    return;
  }

  // Timeouts curtos: o pior caso de bloqueio do laço de aquisição precisa ficar
  // bem abaixo do período de amostragem útil.
  http.setConnectTimeout(1200);
  http.setTimeout(1200);
  http.setReuse(false);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("User-Agent", "ESP32-PlateMonitor/2.0");

  int httpCode = http.POST(payload);

  if (httpCode == 200) {
    falhasConsecutivasHttp = 0;
    Serial.print("[HTTP 200] Telemetria enviada: ");
    Serial.println(payload);
    acionarLedPulso(); // Pulso indicando envio com sucesso
  } else {
    falhasConsecutivasHttp++;
    Serial.print("[HTTP ERRO] Código: ");
    Serial.print(httpCode);
    if (httpCode < 0) {
      Serial.print(" | ");
      Serial.print(http.errorToString(httpCode));
    }
    Serial.printf(" | Alvo: %s:%d | Dados lidos: %s\n", ipServidorAtivo.c_str(), SERVER_PORT, payload.c_str());
    acionarLedPulso(); // pulso não-bloqueante (piscarLed() usava delay())
    if (httpCode < 0) wifiConectado = (WiFi.status() == WL_CONNECTED);

    // Redescoberta do servidor: bloqueia ~1,5 s, então é feita com folga maior e
    // apenas fora da janela crítica de conversão.
    if (falhasConsecutivasHttp >= 5 && millis() - ultimaBuscaServidor >= 30000) {
      ultimaBuscaServidor = millis();
      Serial.println("[HTTP] Conexão falhou repetidamente. Redescobrindo IP do servidor...");
      buscarServidorAutomatico();
      conversaoEmAndamento = false; // descarta conversão atropelada pelo bloqueio
    }
  }

  http.end();
}

// ── FUNÇÃO: MANUTENÇÃO NÃO-BLOQUEANTE DO WI-FI ──────────────────────────────
// Substitui a chamada bloqueante a conectarWiFi() de dentro do envio.
// WiFi.reconnect() retorna imediatamente; a aquisição continua normalmente.
void manterWiFi() {
  static unsigned long ultimaTentativa = 0;

  if (WiFi.status() == WL_CONNECTED) {
    if (!wifiConectado) {
      wifiConectado = true;
      Serial.print("[WIFI] ✓ Reconectado. IP: ");
      Serial.println(WiFi.localIP());
    }
    return;
  }

  wifiConectado = false;
  if (millis() - ultimaTentativa >= 5000) {
    ultimaTentativa = millis();
    Serial.println("[WIFI] Sem conexão. Tentando reconectar (não-bloqueante)...");
    WiFi.reconnect();
  }
}

// ── FUNÇÃO: CONSULTAR TEMPERATURA-ALVO DE REFERÊNCIA NO FLASK ────────────────
void consultarTemperaturaAlvoServidor() {
  if (!wifiConectado) return;

  String url = "http://" + ipServidorAtivo + ":" + String(SERVER_PORT) + PATH_TEMPERATURA_ALVO;

  WiFiClient client;
  HTTPClient http;
  if (!http.begin(client, url)) {
    return;
  }

  http.setConnectTimeout(1200);
  http.setTimeout(1200);
  http.setReuse(false);
  http.addHeader("User-Agent", "ESP32-PlateMonitor/3.0");

  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      bool definida = doc["definida"] | false;
      if (definida && !doc["temperatura_alvo"].isNull()) {
        float novoAlvo = doc["temperatura_alvo"].as<float>();
        if (!isnan(novoAlvo) && novoAlvo >= 0.0 && novoAlvo <= 100.0) {
          if (!temperaturaAlvoConfigurada || abs(novoAlvo - temperaturaAlvo) > 0.001) {
            Serial.printf("[ALVO] ✓ Nova temperatura-alvo de referência: %.2f °C\n", novoAlvo);
          }
          temperaturaAlvo = novoAlvo;
          temperaturaAlvoConfigurada = true;
        }
      } else {
        if (temperaturaAlvoConfigurada) {
          Serial.println("[ALVO] Temperatura-alvo desmarcada no servidor.");
        }
        temperaturaAlvoConfigurada = false;
      }
    }
  } else {
    // Em caso de falha de comunicação:
    // Mantém o último valor válido recebido (não zera e não gera valor fictício)
    // As aquisições dos sensores T1, T2, T3 e T4 continuam normalmente
    if (httpCode > 0) {
      Serial.printf("[ALVO] Aviso: Servidor retornou código HTTP %d na rota %s\n", httpCode, PATH_TEMPERATURA_ALVO);
    }
  }

  http.end();
}

// ── SETUP ────────────────────────────────────────────────────────────────────
void setup() {
  pinMode(LED_STATUS_PIN, OUTPUT);
  digitalWrite(LED_STATUS_PIN, LOW);

  Serial.begin(115200);
  delay(600);

  Serial.println("\n\n");
  Serial.println("╔════════════════════════════════════════════════════════════╗");
  Serial.println("║   ESP32 #01 - MONITOR DA PLACA E AMBIENTE (T1, T2, T3, T4) ║");
  Serial.println("║   Auto-Discovery UDP + 12 bits Assíncrono + Anti-Spike     ║");
  Serial.println("╚════════════════════════════════════════════════════════════╝");

  pinMode(DHT_PIN, INPUT_PULLUP);
  dht.begin();
  carregarOffsetsCalibracao();
  conectarWiFi();
  descobrirSensores();
  buscarServidorAutomatico();
  consultarTemperaturaAlvoServidor();

  Serial.printf("\n[AQUISIÇÃO] Período %lu ms | Conversão %lu ms | Resolução %u bits\n",
                INTERVALO_LEITURA, TEMPO_CONVERSAO, RESOLUCAO_DS18B20);
  Serial.printf("[FILTRO]    EMA alpha = %.4f  ->  tau = %.2f s (t10-90%% = %.1f s)\n",
                ALPHA_EMA, TAU_EMA_S, TAU_EMA_S * 2.197f);

  Serial.println("\nComandos disponíveis via Serial Monitor:");
  Serial.println("  'A' -> Buscar Servidor Flask na Rede (Auto-Discovery)");
  Serial.println("  'G' -> Iniciar Calibração em Banho de Gelo (0 °C)");
  Serial.println("  'R' -> Resetar Offsets de Calibração para 0.00 °C");
  Serial.println("  'S' -> Exibir Diagnóstico Completo (Bruto vs Final)");
  Serial.println("  (o comando 'C' foi removido: destruía o gradiente da placa)\n");
}

// ── LOOP PRINCIPAL ───────────────────────────────────────────────────────────
void loop() {
  unsigned long agora = millis();
  atualizarLedStatus();

  // A AQUISIÇÃO VEM PRIMEIRO. Tudo que pode bloquear (rede, rescan, calibração)
  // roda depois, e sempre fora da janela em que uma conversão está pendente.
  processarLeiturasAssincronas();
  processarLeituraDHT11();

  // Envio orientado a evento: 1 amostra adquirida = 1 amostra transmitida.
  // Elimina a decimação causada por um temporizador de envio independente do
  // período de aquisição (que descartava ~1 de cada 7 amostras).
  if (novaAmostraDisponivel) {
    novaAmostraDisponivel = false;
    enviarDadosParaServidor();
  }

  // Leitura de Comandos do Serial Monitor
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'A' || cmd == 'a') { buscarServidorAutomatico(); conversaoEmAndamento = false; }
    else if (cmd == 'G' || cmd == 'g') calibrarSensoresGelo();
    else if (cmd == 'R' || cmd == 'r') zerarOffsetsCalibracao();
    else if (cmd == 'S' || cmd == 's') exibirStatusCompleto();
    else if (cmd == 'C' || cmd == 'c') {
      Serial.println("\n[REMOVIDO] O comando 'C' foi eliminado nesta revisão.");
      Serial.println("           Ele igualava T2/T3 ao T1, gravando o gradiente");
      Serial.println("           físico da placa dentro dos offsets de calibração.");
      Serial.println("           Use 'G' (banho de gelo) -- único método válido.\n");
    }
  }

  // Manutenção não-bloqueante do Wi-Fi
  manterWiFi();

  // Re-escaneamento automático se algum sensor estiver faltando.
  // Só roda quando não há conversão pendente, para não atropelar uma amostra.
  if (!conversaoEmAndamento &&
      (!sensoresDisponiveis[0] || !sensoresDisponiveis[1] || !sensoresDisponiveis[2]) &&
      agora - ultimoRescan >= INTERVALO_RESCAN) {
    ultimoRescan = agora;
    descobrirSensores();
  }

  // Consulta periódica desacoplada da temperatura-alvo (a cada 15 segundos)
  if (!conversaoEmAndamento && (agora - ultimoQueryTemperaturaAlvo >= INTERVALO_CONSULTA_ALVO)) {
    ultimoQueryTemperaturaAlvo = agora;
    consultarTemperaturaAlvoServidor();
  }

  delay(5);
}
