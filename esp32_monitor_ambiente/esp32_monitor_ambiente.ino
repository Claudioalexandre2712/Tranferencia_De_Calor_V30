/*
  =============================================================================
  TCC - BANCADA TÉRMICA EXPERIMENTAL (UFR)
  FIRMWARE: ESP32 #02 - Monitor de Base e Banho de Água
  CANAIS:
    - T5: Base / Água #01 (DS18B20 #04 - OneWire D4)
    - T6: Base / Água #02 (DS18B20 #05 - OneWire D4)
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
#include <Preferences.h>

// ── CONFIGURAÇÕES DE REDE E SERVIDOR ─────────────────────────────────────────
#define WIFI_SSID "CLAUDIO 2.4Ghz"
#define WIFI_PASSWORD "enjk8122"

const char* SERVER_HOST = "10.247.140.204";
const uint16_t SERVER_PORT = 5000;
const char* SERVER_PATH = "/api/temperaturas";

// ── PINAGEM DO HARDWARE ──────────────────────────────────────────────────────
#define ONE_WIRE_PIN 4      // Barramento OneWire dos DS18B20 de Base/Água
#define LED_STATUS_PIN 2    // LED azul onboard do ESP32
#define NUM_SENSORES 2      // T5, T6

#define INDICE_T5 0         // Índice do sensor T5 no barramento
#define INDICE_T6 1         // Índice do sensor T6 no barramento

const char* SENSOR_NAMES[NUM_SENSORES] = {
  "T5_BASE_AGUA",
  "T6_BASE_AGUA"
};

// ── INSTÂNCIAS E VARIÁVEIS GLOBAIS ───────────────────────────────────────────
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);
Preferences preferences;

DeviceAddress sensorAddresses[NUM_SENSORES];
float temperaturas[NUM_SENSORES] = {0.0, 0.0};
bool sensoresDisponiveis[NUM_SENSORES] = {false, false};
bool leiturasValidas[NUM_SENSORES] = {false, false};
int errosConsecutivos[NUM_SENSORES] = {0, 0};

bool preferencesDisponiveis = false;
bool wifiConectado = false;

// Offsets de Calibração
float OFFSETS_DS18B20[NUM_SENSORES] = {0.0, 0.0};
const float TEMPERATURA_REFERENCIA_GELO = 0.0;
const uint8_t NUM_AMOSTRAS_CALIBRACAO = 30;
const uint8_t MIN_AMOSTRAS_CALIBRACAO = 24;

// Temporização Não-Bloqueante
const unsigned long INTERVALO_LEITURA = 1000;
const unsigned long INTERVALO_ENVIO = 2000;
const unsigned long INTERVALO_RESCAN = 10000;
const unsigned long TEMPO_CONVERSAO_12BITS = 750;

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

  sensoresDisponiveis[0] = false;
  sensoresDisponiveis[1] = false;
  leiturasValidas[0] = false;
  leiturasValidas[1] = false;
  errosConsecutivos[0] = 0;
  errosConsecutivos[1] = 0;

  if (sensors.getAddress(sensorAddresses[0], INDICE_T5)) {
    sensoresDisponiveis[0] = true;
    Serial.print("  ✓ T5_BASE_AGUA -> ROM: ");
    imprimirEndereco(sensorAddresses[0]);
    Serial.println();
  } else {
    Serial.println("  ✗ T5_BASE_AGUA: Sensor não encontrado no índice 0");
  }

  if (quantidade > 1 && sensors.getAddress(sensorAddresses[1], INDICE_T6)) {
    sensoresDisponiveis[1] = true;
    Serial.print("  ✓ T6_BASE_AGUA -> ROM: ");
    imprimirEndereco(sensorAddresses[1]);
    Serial.println();
  } else {
    Serial.println("  ✗ T6_BASE_AGUA: Sensor não encontrado no índice 1");
  }

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
  if (temAnteriorValida && abs(leituraBruta - leituraAnterior) > 15.0) {
    Serial.println("  [FILTRO] Ruído térmico/elétrico descartado (salto > 15°C)");
    return false;
  }
  return true;
}

// ── FUNÇÃO: DISPARAR E LER TEMPERATURAS (ASSÍNCRONO) ────────────────────────
void processarLeiturasAssincronas() {
  unsigned long agora = millis();

  if (!conversaoEmAndamento && (agora - ultimaLeitura >= INTERVALO_LEITURA)) {
    sensors.requestTemperatures();
    ultimaRequisicaoConversao = agora;
    conversaoEmAndamento = true;
  }

  if (conversaoEmAndamento && (agora - ultimaRequisicaoConversao >= TEMPO_CONVERSAO_12BITS)) {
    conversaoEmAndamento = false;
    ultimaLeitura = agora;

    for (int i = 0; i < NUM_SENSORES; i++) {
      if (!sensoresDisponiveis[i]) continue;

      float leituraBruta = sensors.getTempC(sensorAddresses[i]);
      if (leituraValida(leituraBruta, temperaturas[i], leiturasValidas[i])) {
        temperaturas[i] = leituraBruta + OFFSETS_DS18B20[i];
        leiturasValidas[i] = true;
        errosConsecutivos[i] = 0;
      } else {
        leiturasValidas[i] = false;
        errosConsecutivos[i]++;
        if (errosConsecutivos[i] >= 5) {
          sensoresDisponiveis[i] = false;
        }
      }
    }
  }
}

// ── FUNÇÃO: CARREGAR OFFSETS DA FLASH ────────────────────────────────────────
void carregarOffsetsCalibracao() {
  preferencesDisponiveis = preferences.begin("calibracao", false);
  if (!preferencesDisponiveis) {
    Serial.println("[PREF] Falha ao acessar memoria flash; offsets zerados.");
    return;
  }
  OFFSETS_DS18B20[0] = preferences.getFloat("t5", 0.0);
  OFFSETS_DS18B20[1] = preferences.getFloat("t6", 0.0);
  Serial.println("[PREF] Offsets de calibração T5/T6 carregados com sucesso.");
}

// ── FUNÇÃO: CALIBRAÇÃO EM BANHO DE GELO (0 °C) ──────────────────────────────
void calibrarSensoresGelo() {
  float somas[NUM_SENSORES] = {0.0, 0.0};
  uint8_t amostrasValidas[NUM_SENSORES] = {0, 0};
  float offsetsAntigos[NUM_SENSORES];
  float novosOffsets[NUM_SENSORES];

  for (uint8_t i = 0; i < NUM_SENSORES; i++) {
    offsetsAntigos[i] = OFFSETS_DS18B20[i];
    novosOffsets[i] = OFFSETS_DS18B20[i];
  }

  Serial.println("\n╔════════════════════════════════════════════════════╗");
  Serial.println("║       CALIBRAÇÃO POR BANHO DE GELO (0.00 °C)       ║");
  Serial.println("║ T5 e T6 devem estar imersos no gelo fundente.      ║");
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
      float bruta = sensors.getTempC(sensorAddresses[i]);
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
    preferences.putFloat("t5", novosOffsets[0]);
    preferences.putFloat("t6", novosOffsets[1]);
    Serial.println("✓ OFFSETS T5/T6 GRAVADOS COM SUCESSO NA MEMÓRIA FLASH!");
    piscarLed(3, 100);
  }
  Serial.println("--------------------------------\n");
}

// ── FUNÇÃO: RESETAR OFFSETS DE CALIBRAÇÃO ───────────────────────────────────
void zerarOffsetsCalibracao() {
  OFFSETS_DS18B20[0] = 0.0;
  OFFSETS_DS18B20[1] = 0.0;

  if (preferencesDisponiveis) {
    preferences.putFloat("t5", 0.0);
    preferences.putFloat("t6", 0.0);
    Serial.println("[PREF] ✓ Offsets T5/T6 zerados (0.00 °C) na memória flash.");
    piscarLed(2, 150);
  }
}

// ── FUNÇÃO: EXIBIR STATUS COMPLETO NO MONITOR SERIAL ────────────────────────
void exibirStatusCompleto() {
  Serial.println("\n╔════════════════════════════════════════════════════════════╗");
  Serial.println("║          DIAGNÓSTICO DO ESP32 #02 (BASE & ÁGUA)            ║");
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
  StaticJsonDocument<200> doc;

  // Importante: envia apenas t5 e t6 para não sobrescrever t1-t4 do ESP32 #01
  if (leiturasValidas[0]) doc["t5"] = round(temperaturas[0] * 10000) / 10000.0;
  if (leiturasValidas[1]) doc["t6"] = round(temperaturas[1] * 10000) / 10000.0;
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
  http.addHeader("User-Agent", "ESP32-BaseWaterMonitor/2.0");

  int httpCode = http.POST(payload);

  if (httpCode == 200) {
    Serial.print("[HTTP 200] Telemetria enviada: ");
    Serial.println(payload);
    acionarLedPulso();
  } else {
    Serial.print("[HTTP ERRO] Código: ");
    Serial.print(httpCode);
    if (httpCode < 0) {
      Serial.print(" | ");
      Serial.print(http.errorToString(httpCode));
    }
    Serial.println();
    piscarLed(2, 60);
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
  Serial.println("║   ESP32 #02 - MONITOR DE BASE E BANHO DE ÁGUA (T5, T6)     ║");
  Serial.println("║   Firmware Otimizado: 12 bits Assíncrono + Anti-Spike      ║");
  Serial.println("╚════════════════════════════════════════════════════════════╝");

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

  if (WiFi.status() != WL_CONNECTED) {
    wifiConectado = false;
  }

  if (!sensoresDisponiveis[0] && !sensoresDisponiveis[1] &&
      agora - ultimoRescan >= INTERVALO_RESCAN) {
    ultimoRescan = agora;
    descobrirSensores();
  }

  processarLeiturasAssincronas();

  if (agora - ultimoEnvio >= INTERVALO_ENVIO) {
    ultimoEnvio = agora;
    enviarDadosParaServidor();
  }

  delay(20);
}
