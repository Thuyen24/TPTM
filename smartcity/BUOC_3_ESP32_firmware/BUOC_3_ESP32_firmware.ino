/*
 * ============================================================
 * FIRMWARE ESP32 v4.1 — SMART CITY (TỐI ƯU NGUỒN BIÊN)
 * Đề tài : Bảng Điều Khiển Trung Tâm Thành Phố Thông Minh
 * Board  : ESP32 Dev Module (30 pin)
 * Cập nhật: Bỏ hẳn LED Gas (D2) và LED Nước (D4) chống sụt áp.
 * Giữ lại LED Xanh Lá (D13) báo xe và ngắt Hardware Interrupt.
 * ============================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────────────────────
//  CẤU HÌNH WiFi
// ─────────────────────────────────────────────────────────────
const char* WIFI_SSID     = "VIETTEL_";
const char* WIFI_PASSWORD = "123456a@";

// ─────────────────────────────────────────────────────────────
//  CẤU HÌNH MQTT
// ─────────────────────────────────────────────────────────────
const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_CLIENT   = "SmartCity_ESP32_001";
const char* TOPIC_PUB     = "smartcity/sensors";   
const char* TOPIC_VEHICLE = "smartcity/vehicle";   
const char* TOPIC_SUB     = "smartcity/control";   

// ─────────────────────────────────────────────────────────────
//  CHÂN GPIO ĐÃ TỐI ƯU (KHÔNG CÒN LED D2 VÀ D4)
// ─────────────────────────────────────────────────────────────
#define PIN_LED_GREEN  13   // GIỮ LẠI: LED XANH LÁ — Báo xe qua trạm IR (Có trở 220Ω)

// Cảm biến hồng ngoại IR (Ngắt phần cứng)
#define PIN_IR1        18   // Xe VÀO
#define PIN_IR2        19   // Xe RA

// Relay máy bơm (Low Level Trigger — LOW = BẬT bơm)
#define PIN_RELAY      26

// Cảm biến tương tự ADC1 (Đã được giải phóng dòng, cấp điện ổn định)
#define PIN_LDR        32   // Quang trở LDR
#define PIN_ACS712     33   // Cảm biến dòng ACS712
#define PIN_MQ135      34   // Cảm biến khí MQ-135
#define PIN_WATER      35   // Cảm biến mực nước

// ─────────────────────────────────────────────────────────────
//  THÔNG SỐ CẤU HÌNH & NGƯỠNG TỰ ĐỘNG HÓA
// ─────────────────────────────────────────────────────────────
#define IR_DEBOUNCE_MS      80       // Chống rung cơ học cảm biến IR (ms)
#define WATER_DRY_CAL       2400     // Giá trị RAW khi cảm biến nước khô hoàn toàn
#define PUMP_ON_THRESHOLD   70.0     // Mực nước >= 70% → Tự động BẬT máy bơm xả lũ
#define PUMP_OFF_THRESHOLD  50.0     // Mực nước < 50%  → Tự động TẮT máy bơm
#define PUBLISH_INTERVAL    3000     // Chu kỳ gửi dữ liệu cảm biến (3000ms = 3s)
#define LED_GREEN_BLINK     3        // Số lần nháy LED xanh lá khi có sự kiện xe

// ─────────────────────────────────────────────────────────────
//  BIẾN TOÀN CỤC — BIẾN NGẮT ĐẾM XE (volatile)
// ─────────────────────────────────────────────────────────────
volatile int  vehicleCount       = 0;  
volatile int  totalIn            = 0;  
volatile int  totalOut           = 0;  
volatile unsigned long lastIR1Time = 0; 
volatile unsigned long lastIR2Time = 0; 
volatile bool vehicleEventPending  = false; 

// ─────────────────────────────────────────────────────────────
//  BIẾN TOÀN CỤC — HỆ THỐNG
// ─────────────────────────────────────────────────────────────
bool relayState = false;  
bool autoMode   = true;   

WiFiClient   espClient;
PubSubClient mqttClient(espClient);
unsigned long lastPublishTime = 0;

// ============================================================
//  ISR: NGẮT IR1 — XE VÀO
// ============================================================
void IRAM_ATTR onIR1Falling() {
  unsigned long now = millis();
  if (now - lastIR1Time < IR_DEBOUNCE_MS) return; 
  lastIR1Time = now;
  vehicleCount++;
  totalIn++;
  vehicleEventPending = true; 
}

// ============================================================
//  ISR: NGẮT IR2 — XE RA
// ============================================================
void IRAM_ATTR onIR2Falling() {
  unsigned long now = millis();
  if (now - lastIR2Time < IR_DEBOUNCE_MS) return;
  lastIR2Time = now;
  if (vehicleCount > 0) { 
    vehicleCount--;
    totalOut++;
  }
  vehicleEventPending = true;
}

// ============================================================
//  HÀM: NHẤP NHÁY LED XANH LÁ VẬT LÝ BÁO SỰ KIỆN XE
// ============================================================
void blinkGreenLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(PIN_LED_GREEN, HIGH);
    delay(80);
    digitalWrite(PIN_LED_GREEN, LOW);
    delay(80);
  }
}

// ============================================================
//  HÀM: GỬI SỰ KIỆN XE LÊN WEB DASHBOARD NGAY LẬP TỨC
// ============================================================
void publishVehicleEvent() {
  blinkGreenLED(LED_GREEN_BLINK); // Nháy LED xanh lá báo hiệu trực quan trên sa bàn

  if (!mqttClient.connected()) return;

  char buf[200];
  StaticJsonDocument<256> doc;
  doc["device_id"] = MQTT_CLIENT;
  doc["so_xe"]     = vehicleCount;
  doc["total_in"]  = totalIn;
  doc["total_out"] = totalOut;
  doc["timestamp"] = millis();
  serializeJson(doc, buf, sizeof(buf));

  mqttClient.publish(TOPIC_VEHICLE, buf, false); 
  Serial.print("[IR-EVENT] ► Đếm xe: ");
  Serial.println(buf);
}

// ============================================================
//  HÀM: KẾT NỐI WiFi
// ============================================================
void connectWiFi() {
  Serial.print("[WiFi] Kết nối: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retry = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (++retry > 40) {
      Serial.println("\n[WiFi] Thất bại! Khởi động lại ESP32...");
      ESP.restart();
    }
  }
  Serial.print("\n[WiFi] THÀNH CÔNG! IP: ");
  Serial.println(WiFi.localIP());
}

// ============================================================
//  HÀM: CALLBACK MQTT — Nhận lệnh ON/OFF/AUTO bơm từ giao diện Web
// ============================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) message += (char)payload[i];
  message.trim();

  Serial.print("[MQTT] ← Lệnh điều khiển Web: ");
  Serial.println(message);

  if (message == "ON") {
    autoMode = false; relayState = true;
    digitalWrite(PIN_RELAY, LOW); // LOW = BẬT bơm
    Serial.println("[Relay] BƠM BẬT (Thủ công)");
  } else if (message == "OFF") {
    autoMode = false; relayState = false;
    digitalWrite(PIN_RELAY, HIGH); // HIGH = TẮT bơm
    Serial.println("[Relay] BƠM TẮT (Thủ công)");
  } else if (message == "AUTO") {
    autoMode = true;
    Serial.println("[Relay] CHUYỂN CHẾ ĐỘ TỰ ĐỘNG");
  }
}

// ============================================================
//  HÀM: KẾT NỐI MQTT BROKER (HIVEMQ)
// ============================================================
void connectMQTT() {
  int attempts = 0;
  while (!mqttClient.connected() && attempts < 3) {
    Serial.print("[MQTT] Đang kết nối HiveMQ...");
    attempts++;
    if (mqttClient.connect(MQTT_CLIENT)) {
      Serial.println(" THÀNH CÔNG ✓");
      mqttClient.subscribe(TOPIC_SUB);
    } else {
      Serial.print(" THẤT BẠI ✗ rc=");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

// ============================================================
//  HÀM: ĐỌC KHÍ GAS MQ-135 (Lấy trung bình 5 mẫu)
// ============================================================
int readMQ135() {
  long sum = 0;
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_MQ135); delay(1); }
  yield();
  int raw = sum / 5;
  Serial.print("  [MQ-135] Giá trị RAW="); Serial.print(raw);
  
  if (raw <= 2700) {
    Serial.println(" → Khóa baseline: 400 PPM (Sạch)");
    return 400;
  }
  int ppm = constrain(map(raw, 2700, 4095, 400, 5000), 400, 5000);
  Serial.print(" → Ánh xạ: "); Serial.print(ppm); Serial.println(" PPM");
  return ppm;
}

// ============================================================
//  HÀM: ĐỌC MỰC NƯỚC (Lọc nhiễu chống rò điện chai nhựa)
// ============================================================
float readWaterLevel() {
  long sum = 0;
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_WATER); delay(1); }
  yield();
  int raw = sum / 5;
  int thr = WATER_DRY_CAL + 100; // Ngưỡng bắt đầu chạm nước: 2500

  Serial.print("  [WATER] Giá trị RAW="); Serial.print(raw);
  if (raw <= thr) {
    Serial.println(" → Mức ngập: 0.0% (Khô ráo)");
    return 0.0;
  }
  int pct = constrain(map(raw, thr, 4095, 0, 100), 0, 100);
  if (pct <= 40) {
    Serial.print(" → "); Serial.print(pct); Serial.println("% thô → Ép về 0% (Vùng chết lọc nhiễu)");
    return 0.0;
  }
  float finalPct = (float)constrain(map(pct, 40, 100, 0, 100), 0, 100);
  Serial.print(" → Kết quả thực tế: "); Serial.print(finalPct, 1); Serial.println("% (CÓ NGẬP LỤT)");
  return finalPct;
}

// ============================================================
//  HÀM: ĐỌC ÁNH SÁNG LDR
// ============================================================
int readLightSensor() {
  long sum = 0;
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_LDR); delay(1); }
  yield();
  int pct = constrain(map(sum / 5, 4095, 0, 0, 100), 0, 100);
  return pct;
}

// ============================================================
//  HÀM: ĐỌC CÔNG SUẤT ĐIỆN ACS712
// ============================================================
float readPowerConsumption() {
  long sum = 0;
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_ACS712); delayMicroseconds(200); }
  yield();
  float v = (sum / 5.0 / 4095.0) * 3.3 * 1.5;
  float I = (v - 2.5) / 0.185;
  if (abs(I) < 0.05) I = 0.0;
  float power = abs(I) * 220.0;
  return power;
}

// ============================================================
//  HÀM: ĐỌC VÀ ĐẨY ĐỊNH KỲ TOÀN BỘ SENSOR LÊN SERVER
// ============================================================
void publishSensorData() {
  Serial.println("\n--- [3S LUỒNG CHÍNH] ĐỌC CẢM BIẾN ---");

  // Đọc các giá trị cảm biến Analog (Hiện tại dòng điện nuôi rất khỏe và chuẩn xác)
  int   gasLevel = readMQ135();          yield(); delay(10);
  float waterPct = readWaterLevel();     yield(); delay(10);
  int   lightPct = readLightSensor();    yield(); delay(10);
  float power    = readPowerConsumption(); yield(); delay(10);

  bool floodAlert = (waterPct >= PUMP_ON_THRESHOLD);

  // ── ĐIỀU KHIỂN BƠM TỰ ĐỘNG THUẬT TOÁN HYSTERESIS ──
  if (autoMode) {
    if (waterPct >= PUMP_ON_THRESHOLD && !relayState) {
      relayState = true;
      digitalWrite(PIN_RELAY, LOW);  // LOW = KÍCH HOẠT RELAY BẬT BƠM XẢ LŨ
      Serial.println("[AUTO-CONTROL] ⚡ PHÁT HIỆN NGẬP >= 70%: TỰ ĐỘNG BẬT MÁY BƠM!");
    } else if (waterPct < PUMP_OFF_THRESHOLD && relayState) {
      relayState = false;
      digitalWrite(PIN_RELAY, HIGH); // HIGH = NGẮT RELAY TẮT BƠM
      Serial.println("[AUTO-CONTROL] ✓ NƯỚC RÚT < 50%: TỰ ĐỘNG TẮT MÁY BƠM AN TOÀN.");
    }
  }

  // Đọc an toàn dữ liệu xe từ ngắt phần cứng
  noInterrupts();
  int snapCount = vehicleCount;
  int snapIn    = totalIn;
  int snapOut   = totalOut;
  interrupts();

  // Đóng gói payload JSON truyền lên HiveMQ Broker
  char jsonBuffer[512];
  {
    StaticJsonDocument<768> doc;
    doc["device_id"]     = MQTT_CLIENT;
    doc["timestamp"]     = millis();
    doc["nhiet_do"]      = 25.5; // Giả lập do tháo DHT
    doc["do_am"]         = 60.0; // Giả lập do tháo DHT
    doc["chat_luong_kk"] = gasLevel;
    doc["so_xe"]         = snapCount;
    doc["total_in"]      = snapIn;
    doc["total_out"]     = snapOut;
    doc["muc_nuoc"]      = round(waterPct * 10) / 10.0;
    doc["anh_sang"]      = lightPct;
    doc["cong_suat"]     = round(power * 10) / 10.0;
    doc["ngap_lut"]      = floodAlert;
    doc["relay_status"]  = relayState ? "ON" : "OFF";
    doc["relay_mode"]    = autoMode   ? "AUTO" : "MANUAL";
    serializeJson(doc, jsonBuffer, sizeof(jsonBuffer));
  }

  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_PUB, jsonBuffer);
    Serial.println("[MQTT] ✓ Đã gửi gói tin JSON lên Server thành công!");
    Serial.println(jsonBuffer);
  }
}

// ============================================================
//  SETUP — KHỞI TẠO HỆ THỐNG
// ============================================================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n============================================");
  Serial.println("  SMART CITY FIRMWARE V4.1 — TỐI ƯU NGUỒN CƠ BIÊN");
  Serial.println("  ĐÃ GỠ LED D2 & D4 — CHỈ GIỮ LED XE XANH LÁ D13");
  Serial.println("============================================\n");

  // Cấu hình chân Output điều khiển 
  pinMode(PIN_LED_GREEN, OUTPUT);  
  pinMode(PIN_RELAY,     OUTPUT);  

  digitalWrite(PIN_LED_GREEN, LOW);   // Mặc định tắt LED báo xe khi khởi động
  digitalWrite(PIN_RELAY,     HIGH);  // Mặc định TẮT bơm (Sử dụng Relay kích mức Thấp)

  // Cấu hình ngắt phần cứng cho 2 cảm biến hồng ngoại kiểm soát xe
  pinMode(PIN_IR1, INPUT_PULLUP);
  pinMode(PIN_IR2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_IR1), onIR1Falling, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_IR2), onIR2Falling, FALLING);

  // Kết nối mạng
  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(1024);
  connectMQTT();

  Serial.println("[Setup] ✓ Hệ thống đã sẵn sàng thu thập dữ liệu!\n");
}

// ============================================================
//  LOOP — VÒNG LẶP CHÍNH KHÔNG SỬ DỤNG DELAY CHẶN (NON-BLOCKING)
// ============================================================
void loop() {
  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();

  // Nhánh ưu tiên cao: Gửi dữ liệu xe tức thời ngay khi xe chạm cảm biến ngắt
  if (vehicleEventPending) {
    vehicleEventPending = false; 
    publishVehicleEvent();
  }

  // Nhánh định kỳ: Thu thập dữ liệu khí gas, mực nước, ánh sáng và đẩy lên Web sau mỗi 3 giây
  unsigned long now = millis();
  if (now - lastPublishTime >= PUBLISH_INTERVAL) {
    lastPublishTime = now;
    publishSensorData();
  }

  if (now < lastPublishTime) lastPublishTime = now; // Khử tràn bộ đếm millis()

  delay(5); // Cấp thời gian xử lý nhỏ cho trình quản lý MQTT nền
}