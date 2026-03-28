/*
 * SafeWarehouse – AICSS CP4
 * Hardware: Arduino Mega 2560
 *
 * Sensores:
 *   DHT11   → Pino 22 (temperatura e umidade)
 *   HC-SR04 → Pino 24 (Trigger), Pino 26 (Echo)
 *
 * Atuadores:
 *   Módulo LED RGB KS:
 *     R → Pino 28  (vermelho: RISCO)
 *     G → Pino 30  (verde: SEGURO)
 *     B → Pino 32  (não utilizado)
 *   Buzzer Ativo → Pino 34  (alerta sonoro em RISCO)
 *   LCD QAPASS 16x2 I2C → SDA=20, SCL=21 (endereço 0x27)
 *
 * Saída Serial: 115200 baud — formato CSV
 *   Cabeçalho: temp,umidade,distancia,estado
 *   Dados:     24.0,40,100,SEGURO
 *
 * Frequência de leitura: 1 vez por minuto
 */

#include <DHT.h>
#include <LiquidCrystal_I2C.h>

// ─── Pinos (NÃO ALTERAR — hardware já montado) ────────────────────────────────
#define DHT_PIN      22
#define DHT_TYPE     DHT11
#define TRIG_PIN     24
#define ECHO_PIN     26
#define RGB_R        28
#define RGB_G        30
#define RGB_B        32
#define BUZZER_PIN   34

// ─── Configuração ─────────────────────────────────────────────────────────────
#define LEITURA_INTERVAL  2000UL  // 1 minuto em milissegundos
#define DISTANCE_RISCO    30       // cm — distância abaixo deste valor = RISCO
#define LCD_ADDR          0x27     // endereço I2C do módulo QAPASS (tente 0x3F se não funcionar)

// ─── Objetos globais ──────────────────────────────────────────────────────────
DHT dht(DHT_PIN, DHT_TYPE);
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);

unsigned long lastLeitura = 0;
bool primeiraLeitura = true;

// ─── Leitura HC-SR04 ──────────────────────────────────────────────────────────
int readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return 400;          // sem eco = objeto muito distante
  return (int)(duration * 0.034 / 2);
}

// ─── Helpers RGB ──────────────────────────────────────────────────────────────
void rgbSet(bool r, bool g, bool b) {
  digitalWrite(RGB_R, r ? HIGH : LOW);
  digitalWrite(RGB_G, g ? HIGH : LOW);
  digitalWrite(RGB_B, b ? HIGH : LOW);
}

// ─── Atualiza LCD ─────────────────────────────────────────────────────────────
// Linha 0: "T:24.5C  U:60%  "
// Linha 1: "D:15cm  RISCO!  "
void updateLCD(float temp, int hum, int dist, bool risco) {
  lcd.setCursor(0, 0);
  lcd.print(F("T:"));
  lcd.print(temp, 1);
  lcd.print((char)223);   // símbolo °
  lcd.print(F("C U:"));
  lcd.print(hum);
  lcd.print(F("%   "));

  lcd.setCursor(0, 1);
  lcd.print(F("D:"));
  lcd.print(dist);
  lcd.print(F("cm "));
  if (risco) {
    lcd.print(F("RISCO!  "));
  } else {
    lcd.print(F("SEGURO  "));
  }
}

// ─── Setup ────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(RGB_R,      OUTPUT);
  pinMode(RGB_G,      OUTPUT);
  pinMode(RGB_B,      OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(TRIG_PIN,   OUTPUT);
  pinMode(ECHO_PIN,   INPUT);

  // Estado inicial seguro
  rgbSet(false, true, false);
  noTone(BUZZER_PIN);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print(F("SafeWarehouse"));
  lcd.setCursor(0, 1);
  lcd.print(F("Iniciando..."));

  dht.begin();
  delay(2000);   // DHT11 precisa de ~1s para estabilizar
  lcd.clear();

  // Cabeçalho CSV — impresso uma única vez para captura no PC
  Serial.println(F("temp,umidade,distancia,estado"));
}

// ─── Loop ─────────────────────────────────────────────────────────────────────
void loop() {
  unsigned long agora = millis();

  // Lê sensores na primeira execução e depois a cada 1 minuto
  if (primeiraLeitura || (agora - lastLeitura >= LEITURA_INTERVAL)) {
    lastLeitura    = agora;
    primeiraLeitura = false;

    // Leitura DHT11
    float temp = dht.readTemperature();
    float hum  = dht.readHumidity();

    if (isnan(temp) || isnan(hum)) {
      lcd.setCursor(0, 0);
      lcd.print(F("Erro sensor DHT "));
      lcd.setCursor(0, 1);
      lcd.print(F("Tentando...     "));
      return;   // aguarda próximo ciclo sem imprimir dado inválido
    }

    // Leitura HC-SR04
    int dist = readDistance();

    // ── Classificação SEGURO / RISCO ──────────────────────────────────────────
    // RISCO: distância menor que o limite definido (presença detectada)
    bool risco = (dist < DISTANCE_RISCO);

    // ── Atuadores ─────────────────────────────────────────────────────────────
    if (risco) {
      rgbSet(true, false, false);   // LED vermelho
      tone(BUZZER_PIN, 1000);       // buzzer contínuo enquanto há risco
    } else {
      rgbSet(false, true, false);   // LED verde
      noTone(BUZZER_PIN);
    }

    // ── Display LCD ───────────────────────────────────────────────────────────
    updateLCD(temp, (int)hum, dist, risco);

    // ── Saída CSV via Serial (capturada pelo PC / Python) ─────────────────────
    Serial.print(temp, 1);
    Serial.print(F(","));
    Serial.print((int)hum);
    Serial.print(F(","));
    Serial.print(dist);
    Serial.print(F(","));
    Serial.println(risco ? F("RISCO") : F("SEGURO"));
  }
}
