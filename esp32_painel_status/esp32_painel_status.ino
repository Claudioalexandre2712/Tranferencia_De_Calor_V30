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
  RECURSOS AVANÇADOS IMPLEMENTADOS:
    1. Conversão Assíncrona Não-Bloqueante (sem delays travando o processador)
    2. Resolução Máxima de 12 bits (passo de 0.0625 °C)
    3. Filtro Anti-Spike e Validação Térmica
    4. LED de Status Onboard (GPIO 2):
       - Piscando Rápido: Conectando Wi-Fi
       - 1 Pulso a cada 2s: Envio de telemetria com sucesso
       - 2 Pulsos rápidos: Alerta de sensor ou rede
    5. Menu Serial Interativo:
       - 'G' ou 'g': Calibração em Banho de Gelo (0 °C) em 30 amostras
       - 'R' ou 'r': Resetar offsets de calibração para 0.00 °C
       - 'S' ou 's': Exibir Status Completo de Diagnóstico
  =============================================================================
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Preferences.h>

// ── CONFIGURAÇÕES DE REDE E SERVIDOR ─────────────────────────────────────────
#define WIFI_SSID "CLAUDIO 2.4Ghz"
#define WIFI_PASSWORD "enjk8122"

const char* SERVER_HOST = "10.247.140.204";
const uint16_t SERVER_PORT = 5000;
const char* SERVER_PATH = "/api/temperaturas";

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

float temperaturaAmbiente = 0.0;
float umidadeAmbiente = 0.0;
bool temperaturaAmbienteValida = false;
bool preferencesDisponiveis = false;
bool wifiConectado = false;

// Offsets de Calibração
float OFFSETS_DS18B20[NUM_SENSORES] = {0.0, 0.0, 0.0};
const float OFFSET_DHT11 = 0.0;
const float TEMPERATURA_REFERENCIA_GELO = 0.0;
const uint8_t NUM_AMOSTRAS_CALIBRACAO = 30;
const uint8_t MIN_AMOSTRAS_CALIBRACAO = 24;

// Temporização Não-Bloqueante
const unsigned long INTERVALO_LEITURA = 1000;
const unsigned long INTERVALO_ENVIO = 2000;
const unsigned long INTERVALO_RESCAN = 10000;
const unsigned long TEMPO_CONVERSAO_12BITS = 750; // ms para 12 bits

unsigned long ultimaRequisicaoConversao = 0;
bool conversaoEmAndamento = false;
unsigned long ultimaLeitura = 0;
unsigned long ultimoEnvio = 0;
unsigned long ultimoRescan = 0;
unsigned long ledApagarTimestamp = 0;

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
  ledApagarTimestamp = millis() + 100;
}

void atualizarLedStatus() {
  if (ledApagarTimestamp > 0 && millis() >= ledApagarTimestamp) {
    digitalWrite(LED_STATUS_PIN, LOW);
    ledApagarTimestamp = 0;
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

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 25) {
    delay(400);
    digitalWrite(LED_STATUS_PIN, !digitalRead(LED_STATUS_PIN));
    Serial.print(".");
    tentativas++;
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

// ── FUNÇÃO: DESCOBRIR SENSORES DS18B20 ───────────────────────────────────────
void descobrirSensores() {
  sensors.begin();
  delay(50);
  int quantidade = sensors.getDeviceCount();

  Serial.println("\n--- [BUSCA DE SENSORES ONE-WIRE (12 BITS)] ---");
  Serial.print("DS18B20 encontrados no barramento: ");
  Serial.println(quantidade);

  for (int i = 0; i < NUM_SENSORES; i++) {
    sensoresDisponiveis[i] = false;
    leiturasValidas[i] = false;
    errosConsecutivos[i] = 0;

    for (int encontrado = 0; encontrado < quantidade; encontrado++) {
      DeviceAddress enderecoEncontrado;
      if (sensors.getAddress(enderecoEncontrado, encontrado)) {
        bool corresponde = true;
        for (uint8_t byte = 0; byte < 8; byte++) {
          if (enderecoEncontrado[byte] != ENDERECOS_SENSOR[i][byte]) {
            corresponde = false;
            break;
          }
        }
        if (corresponde) {
          memcpy(enderecosReais[i], enderecoEncontrado, sizeof(DeviceAddress));
          sensoresDisponiveis[i] = true;
          Serial.print("  ✓ ");
          Serial.print(SENSOR_NAMES[i]);
          Serial.print(" -> ROM: ");
          imprimirEndereco(enderecosReais[i]);
          Serial.println();
          break;
        }
      }
    }

    // Fallback inteligente: se não encontrou pela ROM fixa, vincula pelo índice disponível
    if (!sensoresDisponiveis[i] && i < quantidade) {
      if (sensors.getAddress(enderecosReais[i], i)) {
        sensoresDisponiveis[i] = true;
        Serial.print("  ⚠ [FALLBACK] ");
        Serial.print(SENSOR_NAMES[i]);
        Serial.print(" -> Vinculado ao indice ");
        Serial.print(i);
        Serial.print(" (ROM: ");
        imprimirEndereco(enderecosReais[i]);
        Serial.println(")");
      }
    }
  }

  // Configura resolução máxima de 12 bits (0.0625°C) e modo não-bloqueante
  sensors.setResolution(12);
  sensors.setWaitForConversion(false);
  Serial.println("✓ Resolução configurada para 12 bits (0.0625 °C) em modo assíncrono.");
  Serial.println("----------------------------------------------\n");
}

// ── FUNÇÃO: VALIDAÇÃO METROLÓGICA E ANTI-SPIKE ──────────────────────────────
bool leituraValida(float leituraBruta, float leituraAnterior, bool temAnteriorValida) {
  if (leituraBruta == DEVICE_DISCONNECTED_C || leituraBruta == 85.0 || leituraBruta < -40.0 || leituraBruta > 130.0) {
    return false;
  }
  // Filtro Anti-Spike: se já existia leitura estável, descarta salto absurdo (> 15°C em 1s)
  if (temAnteriorValida && abs(leituraBruta - leituraAnterior) > 15.0) {
    Serial.println("  [FILTRO] Ruído térmico/elétrico descartado (salto > 15°C)");
    return false;
  }
  return true;
}

// ── FUNÇÃO: DISPARAR E LER TEMPERATURAS (ASSÍNCRONO) ────────────────────────
void processarLeiturasAssincronas() {
  unsigned long agora = millis();

  // Fase 1: Disparar requisição de conversão não-bloqueante
  if (!conversaoEmAndamento && (agora - ultimaLeitura >= INTERVALO_LEITURA)) {
    sensors.requestTemperatures();
    ultimaRequisicaoConversao = agora;
    conversaoEmAndamento = true;
  }

  // Fase 2: Coletar leituras quando passar o tempo de conversão (750ms)
  if (conversaoEmAndamento && (agora - ultimaRequisicaoConversao >= TEMPO_CONVERSAO_12BITS)) {
    conversaoEmAndamento = false;
    ultimaLeitura = agora;

    // Coleta dos 3 DS18B20
    for (int i = 0; i < NUM_SENSORES; i++) {
      if (!sensoresDisponiveis[i]) continue;

      float leituraBruta = sensors.getTempC(enderecosReais[i]);
      if (leituraValida(leituraBruta, temperaturas[i], leiturasValidas[i])) {
        temperaturas[i] = leituraBruta + OFFSETS_DS18B20[i];
        leiturasValidas[i] = true;
        errosConsecutivos[i] = 0;
      } else {
        leiturasValidas[i] = false;
        errosConsecutivos[i]++;
        if (errosConsecutivos[i] >= 5) {
          sensoresDisponiveis[i] = false; // Força nova busca
        }
      }
    }

    // Leitura do DHT11 com filtro
    float tDht = dht.readTemperature();
    float uDht = dht.readHumidity();

    if (!isnan(tDht) && tDht > -20.0 && tDht < 70.0) {
      temperaturaAmbiente = tDht + OFFSET_DHT11;
      temperaturaAmbienteValida = true;
    } else {
      temperaturaAmbienteValida = false;
    }

    if (!isnan(uDht) && uDht >= 0.0 && uDht <= 100.0) {
      umidadeAmbiente = uDht;
    }
  }
}

// ── FUNÇÃO: CARREGAR OFFSETS DA FLASH (PREFERENCES) ──────────────────────────
void carregarOffsetsCalibracao() {
  preferencesDisponiveis = preferences.begin("calibracao", false);
  if (!preferencesDisponiveis) {
    Serial.println("[PREF] Falha ao acessar memoria flash; offsets zerados.");
    return;
  }
  OFFSETS_DS18B20[0] = preferences.getFloat("t1", 0.0);
  OFFSETS_DS18B20[1] = preferences.getFloat("t2", 0.0);
  OFFSETS_DS18B20[2] = preferences.getFloat("t3", 0.0);
  Serial.println("[PREF] Offsets de calibração T1/T2/T3 carregados com sucesso.");
}

// ── FUNÇÃO: CALIBRAÇÃO EM BANHO DE GELO (0 °C) ──────────────────────────────
void calibrarSensoresGelo() {
  float somas[NUM_SENSORES] = {0.0, 0.0, 0.0};
  uint8_t amostrasValidas[NUM_SENSORES] = {0, 0, 0};
  float offsetsAntigos[NUM_SENSORES];
  float novosOffsets[NUM_SENSORES];

  for (uint8_t i = 0; i < NUM_SENSORES; i++) {
    offsetsAntigos[i] = OFFSETS_DS18B20[i];
    novosOffsets[i] = OFFSETS_DS18B20[i];
  }

  Serial.println("\n╔════════════════════════════════════════════════════╗");
  Serial.println("║       CALIBRAÇÃO POR BANHO DE GELO (0.00 °C)       ║");
  Serial.println("║ T1, T2 e T3 devem estar imersos no gelo fundente.  ║");
  Serial.println("║ Coletando 30 amostras em 30 segundos...            ║");
  Serial.println("╚════════════════════════════════════════════════════╝");

  sensors.setWaitForConversion(true);
  for (uint8_t amostra = 0; amostra < NUM_AMOSTRAS_CALIBRACAO; amostra++) {
    sensors.requestTemperatures();
    digitalWrite(LED_STATUS_PIN, !digitalRead(LED_STATUS_PIN));
    Serial.print("Amostra ");
    Serial.print(amostra + 1);
    Serial.print("/");
    Serial.println(NUM_AMOSTRAS_CALIBRACAO);

    for (uint8_t i = 0; i < NUM_SENSORES; i++) {
      if (!sensoresDisponiveis[i]) continue;
      float bruta = sensors.getTempC(enderecosReais[i]);
      if (bruta != DEVICE_DISCONNECTED_C && bruta != 85.0 && bruta > -40.0 && bruta < 60.0) {
        somas[i] += bruta;
        amostrasValidas[i]++;
      }
    }
    delay(950);
  }
  digitalWrite(LED_STATUS_PIN, LOW);
  sensors.setWaitForConversion(false);

  bool algumOffsetSalvo = false;
  Serial.println("\n--- RESULTADOS DA CALIBRAÇÃO ---");
  for (uint8_t i = 0; i < NUM_SENSORES; i++) {
    Serial.print(SENSOR_NAMES[i]);
    Serial.print(" | Amostras: ");
    Serial.print(amostrasValidas[i]);

    if (amostrasValidas[i] >= MIN_AMOSTRAS_CALIBRACAO) {
      float media = somas[i] / amostrasValidas[i];
      novosOffsets[i] = TEMPERATURA_REFERENCIA_GELO - media;
      OFFSETS_DS18B20[i] = novosOffsets[i];
      Serial.print(" | Média: ");
      Serial.print(media, 4);
      Serial.print(" °C | Novo Offset: ");
      Serial.print(novosOffsets[i], 4);
      Serial.println(" °C [OK]");
      algumOffsetSalvo = true;
    } else {
      Serial.println(" | [FALHA: Amostras insuficientes]");
    }
  }

  if (algumOffsetSalvo && preferencesDisponiveis) {
    preferences.putFloat("t1", novosOffsets[0]);
    preferences.putFloat("t2", novosOffsets[1]);
    preferences.putFloat("t3", novosOffsets[2]);
    Serial.println("✓ OFFSETS GRAVADOS COM SUCESSO NA MEMÓRIA FLASH!");
    piscarLed(3, 100);
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
    Serial.println("[PREF] ✓ Offsets T1/T2/T3 zerados (0.00 °C) na memória flash.");
    piscarLed(2, 150);
  }
}

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
  Serial.print(SERVER_HOST);
  Serial.print(":");
  Serial.print(SERVER_PORT);
  Serial.println(SERVER_PATH);
  Serial.println("\n--- LEITURAS ATUAIS (12 BITS) ---");

  for (int i = 0; i < NUM_SENSORES; i++) {
    Serial.print("  ");
    Serial.print(SENSOR_NAMES[i]);
    Serial.print(": ");
    if (leiturasValidas[i]) {
      Serial.print(temperaturas[i], 4);
      Serial.print(" °C (Offset: ");
      Serial.print(OFFSETS_DS18B20[i], 4);
      Serial.println(" °C)");
    } else {
      Serial.println("ERRO / Desconectado");
    }
  }

  Serial.print("  T4_AMBIENTE (DHT11): ");
  if (temperaturaAmbienteValida) {
    Serial.print(temperaturaAmbiente, 2);
    Serial.print(" °C | Umidade: ");
    Serial.print(umidadeAmbiente, 1);
    Serial.println(" %");
  } else {
    Serial.println("ERRO / DHT11 Sem Leitura");
  }

  Serial.print("Memória RAM Livre: ");
  Serial.print(esp_get_free_heap_size());
  Serial.println(" bytes");
  Serial.println("============================================================\n");
}

// ── FUNÇÃO: ENVIAR DADOS VIA HTTP POST PARA O FLASK ─────────────────────────
void enviarDadosParaServidor() {
  if (!wifiConectado) {
    conectarWiFi();
    if (!wifiConectado) return;
  }

  String url = "http://" + String(SERVER_HOST) + ":" + String(SERVER_PORT) + SERVER_PATH;
  StaticJsonDocument<280> doc;

  if (leiturasValidas[0]) doc["t1"] = round(temperaturas[0] * 10000) / 10000.0;
  if (leiturasValidas[1]) doc["t2"] = round(temperaturas[1] * 10000) / 10000.0;
  if (leiturasValidas[2]) doc["t3"] = round(temperaturas[2] * 10000) / 10000.0;
  if (temperaturaAmbienteValida) doc["t4"] = round(temperaturaAmbiente * 10000) / 10000.0;
  if (umidadeAmbiente > 0.0) doc["umidade"] = round(umidadeAmbiente * 10) / 10.0;
  doc["timestamp"] = millis();

  String payload;
  serializeJson(doc, payload);

  WiFiClient client;
  HTTPClient http;
  if (!http.begin(client, url)) {
    Serial.println("[HTTP] Falha ao iniciar conexão HTTP.");
    return;
  }

  http.setConnectTimeout(3000);
  http.setTimeout(3000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("User-Agent", "ESP32-PlateMonitor/2.0");

  int httpCode = http.POST(payload);

  if (httpCode == 200) {
    Serial.print("[HTTP 200] Telemetria enviada: ");
    Serial.println(payload);
    acionarLedPulso(); // Pulso indicando envio com sucesso
  } else {
    Serial.print("[HTTP ERRO] Código: ");
    Serial.print(httpCode);
    if (httpCode < 0) {
      Serial.print(" | ");
      Serial.print(http.errorToString(httpCode));
    }
    Serial.println();
    piscarLed(2, 60); // 2 piscadas de aviso
    if (httpCode < 0) wifiConectado = (WiFi.status() == WL_CONNECTED);
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
  Serial.println("║   Firmware Otimizado: 12 bits Assíncrono + Anti-Spike      ║");
  Serial.println("╚════════════════════════════════════════════════════════════╝");

  dht.begin();
  carregarOffsetsCalibracao();
  conectarWiFi();
  descobrirSensores();

  Serial.println("Comandos disponíveis via Serial Monitor:");
  Serial.println("  'G' -> Iniciar Calibração em Banho de Gelo (0 °C)");
  Serial.println("  'R' -> Resetar Offsets de Calibração");
  Serial.println("  'S' -> Exibir Diagnóstico Completo\n");
}

// ── LOOP PRINCIPAL ───────────────────────────────────────────────────────────
void loop() {
  unsigned long agora = millis();
  atualizarLedStatus();

  // Leitura de Comandos do Serial Monitor
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'G' || cmd == 'g') calibrarSensoresGelo();
    else if (cmd == 'R' || cmd == 'r') zerarOffsetsCalibracao();
    else if (cmd == 'S' || cmd == 's') exibirStatusCompleto();
  }

  // Manutenção periódica do Wi-Fi
  if (WiFi.status() != WL_CONNECTED) {
    wifiConectado = false;
  }

  // Re-escaneamento automático se nenhum sensor responder
  if (!sensoresDisponiveis[0] && !sensoresDisponiveis[1] && !sensoresDisponiveis[2] &&
      agora - ultimoRescan >= INTERVALO_RESCAN) {
    ultimoRescan = agora;
    descobrirSensores();
  }

  // Processamento contínuo não-bloqueante de leitura
  processarLeiturasAssincronas();

  // Envio de telemetria no intervalo configurado (2.0s)
  if (agora - ultimoEnvio >= INTERVALO_ENVIO) {
    ultimoEnvio = agora;
    enviarDadosParaServidor();
  }

  delay(20);
}
