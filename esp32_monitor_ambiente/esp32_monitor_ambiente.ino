/*
  =============================================================================
  TCC - BANCADA TÉRMICA EXPERIMENTAL (UFR)
  FIRMWARE: ESP32 #02 - Monitor de Base e Banho de Água
  CANAIS:
    - T5: Base / Água #01 (DS18B20 #04 - OneWire D4)
    - T6: Base / Água #02 (DS18B20 #05 - OneWire D4)
  =============================================================================
  RECURSOS IMPLEMENTADOS:
    1. Conversão Assíncrona Não-Bloqueante com período de amostragem REAL fechado
    2. Resolução de 12 bits (passo de 0.0625 °C) -- ver RESOLUCAO_DS18B20
    3. Validação Anti-Spike por TAXA (°C/s) e descarte de conversão obsoleta
    4. Vinculação por ROM Address APRENDIDA e persistida em flash
    5. Envio orientado a evento: 1 amostra adquirida = 1 amostra transmitida
    6. Menu Serial Interativo:
       - 'G' ou 'g': Calibração em Banho de Gelo (0 °C) -- ÚNICO método válido
       - 'R' ou 'r': Resetar offsets de calibração para 0.00 °C
       - 'S' ou 's': Exibir Status Completo de Diagnóstico
       - 'M' ou 'm': Re-aprender o mapeamento ROM -> T5/T6
       - 'A' ou 'a': Buscar servidor Flask na rede
  =============================================================================
  REVISÃO METROLÓGICA (auditoria):
    - CORRIGIDO: o rescan exigia que AMBOS os sensores sumissem (&&). Com isso,
      a perda de um único sensor congelava aquele canal permanentemente, e o
      último valor continuava a ser publicado como se fosse atual.
    - CORRIGIDO: T5/T6 eram vinculados por ordem de descoberta do OneWire, sem
      nenhuma rastreabilidade. Agora os ROMs são aprendidos uma vez e gravados.
    - O comando 'C' (igualar T5 ao T6) foi REMOVIDO.
  =============================================================================
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>
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
#define ONE_WIRE_PIN 4      // Barramento OneWire dos DS18B20 de Base/Água
#define LED_STATUS_PIN 2    // LED azul onboard do ESP32
#define NUM_SENSORES 2      // T5, T6

// (Os antigos INDICE_T5/INDICE_T6 foram removidos: a posição no barramento não
//  identifica o sensor. A vinculação agora é por ROM Address gravado em flash.)

const char* SENSOR_NAMES[NUM_SENSORES] = {
  "T5_BASE_AGUA",
  "T6_BASE_AGUA"
};

// ── INSTÂNCIAS E VARIÁVEIS GLOBAIS ───────────────────────────────────────────
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);
Preferences preferences;

// ROM Address de cada canal. Diferente do ESP32 #01, aqui os ROMs não são
// conhecidos em tempo de compilação: são APRENDIDOS na primeira inicialização e
// gravados na flash. A partir daí a vinculação T5/T6 é por ROM, e não pela ordem
// de descoberta do OneWire (que não é uma propriedade física do sensor).
DeviceAddress sensorAddresses[NUM_SENSORES];
bool romConhecido[NUM_SENSORES] = {false, false};

float temperaturas[NUM_SENSORES] = {0.0, 0.0};
bool sensoresDisponiveis[NUM_SENSORES] = {false, false};
bool leiturasValidas[NUM_SENSORES] = {false, false};
int errosConsecutivos[NUM_SENSORES] = {0, 0};

bool preferencesDisponiveis = false;
bool wifiConectado = false;

// Offsets de Calibração
float OFFSETS_DS18B20[NUM_SENSORES] = {0.0, 0.0};

// ── OFFSETS DE REFERÊNCIA (BANHO DE GELO VÁLIDO) ─────────────────────────────
// Resultado de uma calibração em gelo fundente efetivamente realizada, com
// 30/30 amostras válidas por sensor, em 12 bits:
//
//   T5_BASE_AGUA | Média: +0.0604 °C | Offset: -0.0604 °C
//   T6_BASE_AGUA | Média: +0.0625 °C | Offset: -0.0625 °C
//
// Rastreabilidade: T5 = 29 amostras em +0.0625 °C e 1 em 0.0000 °C
// (29 × 0.0625 / 30 = 0.0604166...); T6 = 30 amostras em +0.0625 °C (1 LSB).
// Ambos são um viés de apenas 1 LSB: calibração de qualidade exemplar, muito
// dentro da especificação do DS18B20 (±0,5 °C).
//
// Usados como PADRÃO quando a flash não contém calibração. 'G' sobrescreve.
// ATENÇÃO: só válidos para ESTES probes nestas posições.
const float OFFSETS_PADRAO_GELO[NUM_SENSORES] = {-0.0604f, -0.0625f};
const float TEMPERATURA_REFERENCIA_GELO = 0.0;
const uint8_t NUM_AMOSTRAS_CALIBRACAO = 30;
const uint8_t MIN_AMOSTRAS_CALIBRACAO = 24;

// Validação da calibração em gelo (ver comentários equivalentes no ESP32 #01)
const float JANELA_AMOSTRA_GELO = 5.0f;
const float MAX_MEDIA_GELO      = 2.0f;
const float MAX_OFFSET_ACEITO   = 1.5f;

// Invalida automaticamente offsets gravados por firmwares anteriores.
const uint32_t CALIB_VERSAO = 2;

// ── RESOLUÇÃO DOS DS18B20 ────────────────────────────────────────────────────
// 12 bits = 0.0625 °C / 750 ms   11 bits = 0.125 °C / 375 ms
// 10 bits = 0.2500 °C / 188 ms    9 bits = 0.500 °C /  94 ms
const uint8_t  RESOLUCAO_DS18B20  = 12;
const unsigned long TEMPO_CONVERSAO = 750;  // ms; DEVE casar com RESOLUCAO_DS18B20

// ── RASTREABILIDADE METROLÓGICA E FILTRO DIGITAL EMA ─────────────────────────
// Cadeia metrológica:
// 1. Leitura Física (Raw) -> 2. Validação Anti-Spike -> 3. Calibração (Offset) -> 4. EMA -> 5. Valor Filtrado Final
float temperaturasRaw[NUM_SENSORES] = {0.0, 0.0};        // Leitura física direta do DS18B20 (sem offset e sem filtro)
float temperaturasCalibradas[NUM_SENSORES] = {0.0, 0.0}; // Dado experimental com offset de calibração preservado
float temperaturasFiltradas[NUM_SENSORES] = {0.0, 0.0};  // Valor suavizado pelo filtro EMA
bool emaIniciado[NUM_SENSORES] = {false, false};         // Flag individual de inicialização do estado do EMA
unsigned long ultimaAtualizacaoValida[NUM_SENSORES] = {0, 0}; // millis da última leitura válida

// ── TEMPORIZAÇÃO NÃO-BLOQUEANTE ──────────────────────────────────────────────
// INTERVALO_LEITURA é medido entre REQUISIÇÕES de conversão, portanto é o
// período de amostragem REAL. Precisa ser > TEMPO_CONVERSAO.
const unsigned long INTERVALO_LEITURA = 1000;
const unsigned long INTERVALO_RESCAN = 6000;
const unsigned long IDADE_MAXIMA_CONVERSAO = 1500;  // descarta conversão atrasada
const unsigned long IDADE_MAXIMA_DADO = 5000;       // não transmite dado mais velho

// Filtro EMA: alpha derivado do período de amostragem REAL.
//   alpha = Δt / (tau + Δt);  com Δt = 1.0 s e tau = 4.0 s  ->  alpha = 0.20
const float TAU_EMA_S = 4.0f;
const float DT_EMA_S  = INTERVALO_LEITURA / 1000.0f;
const float ALPHA_EMA = DT_EMA_S / (TAU_EMA_S + DT_EMA_S);

// Anti-spike expresso como TAXA (idêntico ao ESP32 #01: os dois firmwares
// precisam aplicar o MESMO critério ao mesmo fenômeno).
const float MAX_TAXA_C_POR_S = 10.0f;

unsigned long ultimaRequisicaoConversao = 0;
bool conversaoEmAndamento = false;
unsigned long ultimoRescan = 0;
unsigned long ledApagarTimestamp = 0;
bool ledAceso = false;

// Envio orientado a evento
bool novaAmostraDisponivel = false;
unsigned long instanteAmostra = 0;

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
// Carrega da flash o mapeamento ROM -> canal aprendido anteriormente.
void carregarRomsSalvos() {
  if (!preferencesDisponiveis) return;
  const char* chaves[NUM_SENSORES] = {"rom5", "rom6"};
  for (int i = 0; i < NUM_SENSORES; i++) {
    DeviceAddress tmp;
    size_t lidos = preferences.getBytes(chaves[i], tmp, sizeof(DeviceAddress));
    if (lidos == sizeof(DeviceAddress) && tmp[0] != 0x00 && tmp[0] != 0xFF) {
      memcpy(sensorAddresses[i], tmp, sizeof(DeviceAddress));
      romConhecido[i] = true;
    }
  }
}

// Aprende o mapeamento atual (ordem do barramento) e grava na flash.
// Só deve ser usado com AMBOS os probes conectados e identificados fisicamente.
void aprenderRoms() {
  sensors.begin();
  delay(50);
  int quantidade = sensors.getDeviceCount();

  Serial.println("\n--- [APRENDIZADO DO MAPEAMENTO ROM -> CANAL] ---");
  if (quantidade < NUM_SENSORES) {
    Serial.printf("  ✗ ABORTADO: %d sensor(es) no barramento, são necessários %d.\n",
                  quantidade, NUM_SENSORES);
    Serial.println("    Conecte os dois probes antes de re-aprender.\n");
    return;
  }

  const char* chaves[NUM_SENSORES] = {"rom5", "rom6"};
  for (int i = 0; i < NUM_SENSORES; i++) {
    if (!sensors.getAddress(sensorAddresses[i], i)) continue;
    romConhecido[i] = true;
    if (preferencesDisponiveis) {
      preferences.putBytes(chaves[i], sensorAddresses[i], sizeof(DeviceAddress));
    }
    Serial.printf("  %s -> ROM ", SENSOR_NAMES[i]);
    imprimirEndereco(sensorAddresses[i]);
    Serial.println("  [GRAVADO]");
  }
  Serial.println("  ATENÇÃO: confirme fisicamente qual probe é qual (desconecte um");
  Serial.println("  de cada vez e observe qual canal cai). Se estiver trocado, troque");
  Serial.println("  os probes de posição e use 'M' novamente.\n");
}

void descobrirSensores() {
  sensors.begin();
  delay(50);
  int quantidade = sensors.getDeviceCount();

  Serial.println("\n--- [BUSCA DE SENSORES ONE-WIRE] ---");
  Serial.print("DS18B20 encontrados no barramento: ");
  Serial.println(quantidade);

  // Se ainda não há mapeamento gravado, aprende agora (primeira inicialização).
  if (!romConhecido[0] || !romConhecido[1]) {
    Serial.println("  [INFO] Mapeamento ROM ausente. Aprendendo pela ordem do barramento...");
    aprenderRoms();
  }

  // Vinculação ESTRITA por ROM. Um sensor ausente invalida SOMENTE o seu canal;
  // os demais nunca são remapeados.
  for (int i = 0; i < NUM_SENSORES; i++) {
    leiturasValidas[i] = false;
    errosConsecutivos[i] = 0;

    if (romConhecido[i] && sensors.isConnected(sensorAddresses[i])) {
      sensoresDisponiveis[i] = true;
      Serial.printf("  ✓ %s -> ROM ", SENSOR_NAMES[i]);
      imprimirEndereco(sensorAddresses[i]);
      Serial.println();
    } else {
      sensoresDisponiveis[i] = false;
      Serial.printf("  ✗ %s -> ROM ", SENSOR_NAMES[i]);
      if (romConhecido[i]) imprimirEndereco(sensorAddresses[i]);
      else Serial.print("(desconhecido)");
      Serial.println("  NÃO responde");
    }
  }

  sensors.setResolution(RESOLUCAO_DS18B20);
  sensors.setWaitForConversion(false);
  conversaoEmAndamento = false;  // descarta conversão órfã iniciada antes do rescan
  // Passo do DS18B20 = 2^-(R-8): 12b->0.0625  11b->0.125  10b->0.25  9b->0.5
  Serial.printf("  Resolução: %u bits (passo %.4f °C, conversão %lu ms)\n",
                RESOLUCAO_DS18B20, 1.0f / (1 << (RESOLUCAO_DS18B20 - 8)), TEMPO_CONVERSAO);
  Serial.println("----------------------------------------------\n");
}

// ── FUNÇÃO: VALIDAÇÃO METROLÓGICA E ANTI-SPIKE ──────────────────────────────
bool leituraValida(float leituraBruta, float leituraAnterior, bool temAnteriorValida, unsigned long dtMs) {
  // isnan() acrescentado para ficar idêntico ao ESP32 #01: os dois firmwares
  // precisam rejeitar exatamente o mesmo conjunto de valores inválidos.
  if (isnan(leituraBruta) || leituraBruta == DEVICE_DISCONNECTED_C || leituraBruta == 85.0 ||
      leituraBruta < -40.0 || leituraBruta > 130.0) {
    return false;
  }
  // Anti-Spike por TAXA (mesmo critério do ESP32 #01)
  if (temAnteriorValida && dtMs > 0) {
    float limite = MAX_TAXA_C_POR_S * (dtMs / 1000.0f);
    if (limite < 1.0f) limite = 1.0f;
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

  // Fase 0: Descartar conversão obsoleta (bloqueio de rede, rescan, calibração).
  if (conversaoEmAndamento && (agora - ultimaRequisicaoConversao > IDADE_MAXIMA_CONVERSAO)) {
    Serial.printf("  [TEMPO] Conversão obsoleta (%lu ms) descartada.\n",
                  agora - ultimaRequisicaoConversao);
    conversaoEmAndamento = false;
  }

  // Fase 1: Disparar requisição de conversão não-bloqueante.
  // Período medido entre REQUISIÇÕES = período de amostragem REAL.
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

    // Coleta, validação metrológica, calibração e filtragem EMA dos 2 DS18B20 (T5, T6)
    for (int i = 0; i < NUM_SENSORES; i++) {
      if (!sensoresDisponiveis[i]) continue;

      // 1. Leitura Física Direta do DS18B20, sempre pelo ROM Address
      float leituraFisica = sensors.getTempC(sensorAddresses[i]);

      unsigned long dt = (ultimaAtualizacaoValida[i] > 0)
                       ? (agora - ultimaAtualizacaoValida[i]) : INTERVALO_LEITURA;

      // 2. Validação Metrológica e Rejeição de Anomalias/Spikes
      if (leituraValida(leituraFisica, temperaturasRaw[i], emaIniciado[i], dt)) {
        // Armazena a leitura física pura validada
        temperaturasRaw[i] = leituraFisica;

        // 3. Aplicação do Offset de Calibração Existente (Dado Experimental Preservado)
        temperaturasCalibradas[i] = temperaturasRaw[i] + OFFSETS_DS18B20[i];

        // 4. Filtro EMA Conservador (alpha = 0.20)
        // Primeira leitura válida: Tf = T (Não inicializa com zero)
        if (!emaIniciado[i]) {
          temperaturasFiltradas[i] = temperaturasCalibradas[i];
          emaIniciado[i] = true;
        } else {
          // Ciclos subsequentes: Tf(n) = alpha * T(n) + (1 - alpha) * Tf(n-1)
          temperaturasFiltradas[i] = (ALPHA_EMA * temperaturasCalibradas[i]) + ((1.0f - ALPHA_EMA) * temperaturasFiltradas[i]);
        }

        // 5. Valor Final atribuído para exibição e telemetria
        temperaturas[i] = temperaturasFiltradas[i];
        leiturasValidas[i] = true;
        ultimaAtualizacaoValida[i] = agora;
        errosConsecutivos[i] = 0;
      } else {
        // Leitura inválida: NÃO atualiza o EMA e NÃO substitui o último valor válido.
        errosConsecutivos[i]++;
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

// ── FUNÇÃO: CARREGAR OFFSETS DA FLASH ────────────────────────────────────────
void carregarOffsetsCalibracao() {
  preferencesDisponiveis = preferences.begin("calibracao", false);
  if (!preferencesDisponiveis) {
    Serial.println("[PREF] Falha ao acessar memoria flash; offsets zerados.");
    return;
  }
  // Offsets gravados por firmwares anteriores são DESCARTADOS (ver ESP32 #01).
  uint32_t versaoGravada = preferences.getUInt("ver", 0);
  if (versaoGravada != CALIB_VERSAO) {
    Serial.println("\n  ╔══════════════════════════════════════════════════════════╗");
    Serial.println("  ║  [PREF] CALIBRAÇÃO ANTIGA DETECTADA E DESCARTADA         ║");
    Serial.println("  ║  Offsets zerados. Refaça a calibração com 'G'            ║");
    Serial.println("  ╚══════════════════════════════════════════════════════════╝");
    Serial.printf("  Valores descartados: T5=%+.4f  T6=%+.4f\n",
                  preferences.getFloat("t5", 0.0f), preferences.getFloat("t6", 0.0f));

    // Restaura os offsets do banho de gelo documentado em OFFSETS_PADRAO_GELO.
    Serial.println("  Restaurando offsets do banho de gelo de referência:");
    for (int i = 0; i < NUM_SENSORES; i++) {
      OFFSETS_DS18B20[i] = OFFSETS_PADRAO_GELO[i];
      Serial.printf("       %-16s %+.4f °C\n", SENSOR_NAMES[i], OFFSETS_DS18B20[i]);
    }
    Serial.println("  Confirme com 'G' se algum probe foi trocado de posição.");

    preferences.putFloat("t5", OFFSETS_DS18B20[0]);
    preferences.putFloat("t6", OFFSETS_DS18B20[1]);
    preferences.putUInt("ver", CALIB_VERSAO);
    return;
  }

  OFFSETS_DS18B20[0] = preferences.getFloat("t5", 0.0);
  OFFSETS_DS18B20[1] = preferences.getFloat("t6", 0.0);
  Serial.println("[PREF] Offsets de calibração T5/T6 carregados:");
  for (int i = 0; i < NUM_SENSORES; i++) {
    Serial.printf("       %-16s %+.4f °C%s\n", SENSOR_NAMES[i], OFFSETS_DS18B20[i],
                  (fabsf(OFFSETS_DS18B20[i]) > MAX_OFFSET_ACEITO) ? "   <-- SUSPEITO!" : "");
  }
}

// ── FUNÇÃO: CALIBRAÇÃO EM BANHO DE GELO (0 °C) ──────────────────────────────
void calibrarSensoresGelo() {
  float somas[NUM_SENSORES] = {0.0, 0.0};
  uint8_t amostrasValidas[NUM_SENSORES] = {0, 0};
  uint8_t amostrasForaDoGelo[NUM_SENSORES] = {0, 0};
  float novosOffsets[NUM_SENSORES];

  for (uint8_t i = 0; i < NUM_SENSORES; i++) {
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
      if (bruta == DEVICE_DISCONNECTED_C || bruta == 85.0 || isnan(bruta)) continue;

      Serial.printf("| %s=%.3f ", SENSOR_NAMES[i], bruta);

      // Só aceita amostra compatível com gelo fundente: um probe esquecido fora
      // do banho, a 25 °C, geraria um offset de -25 °C gravado na flash.
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
      Serial.println("                     DS18B20 fora da especificação: substitua o probe.]");
      continue;
    }

    novosOffsets[i] = offsetCandidato;
    OFFSETS_DS18B20[i] = offsetCandidato;
    Serial.printf("| Média: %.4f °C | Novo Offset: %+.4f °C [OK]\n", media, offsetCandidato);
    algumOffsetSalvo = true;
  }

  if (algumOffsetSalvo && preferencesDisponiveis) {
    preferences.putFloat("t5", novosOffsets[0]);
    preferences.putFloat("t6", novosOffsets[1]);
    preferences.putUInt("ver", CALIB_VERSAO);
    Serial.println("✓ OFFSETS T5/T6 GRAVADOS NA MEMÓRIA FLASH.");
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

  if (preferencesDisponiveis) {
    preferences.putFloat("t5", 0.0);
    preferences.putFloat("t6", 0.0);
    preferences.putUInt("ver", CALIB_VERSAO);
    Serial.println("[PREF] ✓ Offsets T5/T6 zerados (0.00 °C) na memória flash.");
    piscarLed(2, 150);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// REMOVIDO: calibrarSensor5ComSensor6() -- antigo comando 'C'
//
// Calculava  OFFSET[T5] = raw_T6 - raw_T5  e gravava na flash, forçando T5 a ler
// exatamente T6. Qualquer diferença térmica real entre os dois pontos de medição
// era assim convertida em viés de calibração e apagada dos ensaios seguintes.
//
// O único método válido é o ponto fixo (banho de gelo): comando 'G'.
// ─────────────────────────────────────────────────────────────────────────────

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
    Serial.print("                    ROM: ");
    if (romConhecido[i]) imprimirEndereco(sensorAddresses[i]); else Serial.print("(não aprendido)");
    Serial.println();
  }

  Serial.printf("\n  Aquisição: %lu ms | Conversão: %lu ms | Resolução: %u bits (passo %.4f °C)\n",
                INTERVALO_LEITURA, TEMPO_CONVERSAO, RESOLUCAO_DS18B20,
                1.0f / (1 << (RESOLUCAO_DS18B20 - 8)));
  Serial.printf("  EMA: alpha = %.4f -> tau = %.2f s\n\n", ALPHA_EMA, TAU_EMA_S);

  Serial.print("Memória RAM Livre: ");
  Serial.print(esp_get_free_heap_size());
  Serial.println(" bytes");
  Serial.println("============================================================\n");
}

// ── FUNÇÃO: ENVIAR DADOS VIA HTTP POST PARA O FLASK ─────────────────────────
void enviarDadosParaServidor() {
  // NÃO chama conectarWiFi() aqui (bloqueia até ~18 s e congela a aquisição).
  if (!wifiConectado) return;

  unsigned long agora = millis();
  String url = "http://" + ipServidorAtivo + ":" + String(SERVER_PORT) + SERVER_PATH;
  StaticJsonDocument<256> doc;

  // Importante: envia apenas t5 e t6 para não sobrescrever t1-t4 do ESP32 #01.
  // Um canal só é transmitido se a leitura for VÁLIDA e RECENTE: a condição
  // antiga ("|| temperaturas[i] > 0.0") republicava indefinidamente o valor de
  // um sensor morto, sem qualquer sinalização de erro.
  const char* chaves[NUM_SENSORES] = {"t5", "t6"};
  for (int i = 0; i < NUM_SENSORES; i++) {
    if (leiturasValidas[i] && (agora - ultimaAtualizacaoValida[i] <= IDADE_MAXIMA_DADO)) {
      doc[chaves[i]] = round(temperaturas[i] * 10000) / 10000.0;
    }
  }
  doc["device"] = "esp32_02";
  doc["timestamp"] = millis();
  doc["amostra_ms"] = instanteAmostra;
  doc["idade_ms"] = agora - instanteAmostra;

  String payload;
  serializeJson(doc, payload);

  WiFiClient client;
  HTTPClient http;
  if (!http.begin(client, url)) {
    Serial.println("[HTTP] Falha ao iniciar conexão HTTP.");
    return;
  }

  http.setConnectTimeout(1200);
  http.setTimeout(1200);
  http.setReuse(false);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("User-Agent", "ESP32-BaseWaterMonitor/3.0");

  int httpCode = http.POST(payload);

  if (httpCode == 200) {
    falhasConsecutivasHttp = 0;
    Serial.print("[HTTP 200] Telemetria enviada: ");
    Serial.println(payload);
    acionarLedPulso();
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

// ── SETUP ────────────────────────────────────────────────────────────────────
void setup() {
  pinMode(LED_STATUS_PIN, OUTPUT);
  digitalWrite(LED_STATUS_PIN, LOW);

  Serial.begin(115200);
  delay(600);

  Serial.println("\n\n");
  Serial.println("╔════════════════════════════════════════════════════════════╗");
  Serial.println("║   ESP32 #02 - MONITOR DE BASE E BANHO DE ÁGUA (T5, T6)     ║");
  Serial.println("║   Auto-Discovery UDP + 12 bits Assíncrono + Anti-Spike     ║");
  Serial.println("╚════════════════════════════════════════════════════════════╝");

  carregarOffsetsCalibracao();
  carregarRomsSalvos();
  conectarWiFi();
  descobrirSensores();
  buscarServidorAutomatico();

  Serial.printf("\n[AQUISIÇÃO] Período %lu ms | Conversão %lu ms | Resolução %u bits\n",
                INTERVALO_LEITURA, TEMPO_CONVERSAO, RESOLUCAO_DS18B20);
  Serial.printf("[FILTRO]    EMA alpha = %.4f  ->  tau = %.2f s (t10-90%% = %.1f s)\n",
                ALPHA_EMA, TAU_EMA_S, TAU_EMA_S * 2.197f);

  Serial.println("\nComandos disponíveis via Serial Monitor:");
  Serial.println("  'A' -> Buscar Servidor Flask na Rede (Auto-Discovery)");
  Serial.println("  'G' -> Iniciar Calibração em Banho de Gelo (0 °C)");
  Serial.println("  'M' -> Re-aprender mapeamento ROM -> T5/T6");
  Serial.println("  'R' -> Resetar Offsets de Calibração");
  Serial.println("  'S' -> Exibir Diagnóstico Completo");
  Serial.println("  (o comando 'C' foi removido: apagava a diferença real T5-T6)\n");
}

// ── LOOP PRINCIPAL ───────────────────────────────────────────────────────────
void loop() {
  unsigned long agora = millis();
  atualizarLedStatus();

  // A AQUISIÇÃO VEM PRIMEIRO. Tudo que pode bloquear roda depois.
  processarLeiturasAssincronas();

  // Envio orientado a evento: 1 amostra adquirida = 1 amostra transmitida.
  if (novaAmostraDisponivel) {
    novaAmostraDisponivel = false;
    enviarDadosParaServidor();
  }

  // Leitura de Comandos do Serial Monitor
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'A' || cmd == 'a') { buscarServidorAutomatico(); conversaoEmAndamento = false; }
    else if (cmd == 'G' || cmd == 'g') calibrarSensoresGelo();
    else if (cmd == 'M' || cmd == 'm') { aprenderRoms(); descobrirSensores(); }
    else if (cmd == 'R' || cmd == 'r') zerarOffsetsCalibracao();
    else if (cmd == 'S' || cmd == 's') exibirStatusCompleto();
    else if (cmd == 'C' || cmd == 'c') {
      Serial.println("\n[REMOVIDO] O comando 'C' foi eliminado nesta revisão.");
      Serial.println("           Ele igualava T5 a T6, apagando a diferença real");
      Serial.println("           entre os dois pontos de medição.");
      Serial.println("           Use 'G' (banho de gelo) -- único método válido.\n");
    }
  }

  // Manutenção não-bloqueante do Wi-Fi
  manterWiFi();

  // CORRIGIDO: era "&&" (exigia que AMBOS os sensores sumissem).
  // Com o "&&", a perda de um único sensor nunca disparava o rescan e aquele
  // canal ficava congelado no último valor até o próximo reboot.
  if (!conversaoEmAndamento &&
      (!sensoresDisponiveis[0] || !sensoresDisponiveis[1]) &&
      agora - ultimoRescan >= INTERVALO_RESCAN) {
    ultimoRescan = agora;
    descobrirSensores();
  }

  delay(5);
}
