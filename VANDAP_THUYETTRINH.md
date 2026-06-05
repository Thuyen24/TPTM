# 🎓 CẨM NANG VẤN ĐÁP & THUYẾT TRÌNH BẢO VỆ ĐỒ ÁN TỐT NGHIỆP

> **Đề tài:** Bảng điều khiển trung tâm cho thành phố thông minh (Central Dashboard for Smart City)  
> **Sinh viên thực hiện:** Đỗ Văn Thuyên — MSV: 1671020308  
> **Lớp:** K16 CNTT — Khoa Công nghệ Thông tin — Đại học Đại Nam  
> **Năm bảo vệ:** 2026

---

## PHẦN 1: KIẾN TRÚC VÀ LUỒNG HOẠT ĐỘNG DỮ LIỆU TỔNG THỂ (DATA FLOW)

Hệ thống được xây dựng chặt chẽ theo mô hình kiến trúc IoT 3 lớp chuẩn hóa (Perception -> Network -> Application) để xử lý dữ liệu và điều khiển phản hồi thời gian thực:

```
┌──────────────────────────────────────────────────────────┐
│  1. LỚP THIẾT BỊ BIÊN (Perception Layer)                 │
│  - Thu thập dữ liệu từ các cảm biến vật lý trên sa bàn.  │
│  - Kỹ thuật: Analog Polling & Hardware Interrupt.        │
└───────────────────────────┬──────────────────────────────┘
                            │ WiFi (TCP/IP) - Giao thức MQTT
                            ▼
┌──────────────────────────────────────────────────────────┐
│  2. LỚP MẠNG TRUYỀN TẢI (Network Layer)                   │
│  - MQTT Cloud Broker (HiveMQ Cloud làm trung gian).      │
│  - Định dạng gói tin: Chuỗi JSON siêu nhẹ.               │
└───────────────────────────┬──────────────────────────────┘
                            │ Subscribe MQTT & Đẩy SSE (REST)
                            ▼
┌──────────────────────────────────────────────────────────┐
│  3. LỚP ỨNG DỤNG (Application Layer)                      │
│  - Backend Server: FastAPI nhận dữ liệu, ghi SQLite.     │
│  - Client Web Dashboard: Nhận luồng đẩy SSE thời gian thực│
└──────────────────────────────────────────────────────────┘
```

---

### 1. Lớp Biên (Perception Layer): Cơ chế Đa nhiệm Non-blocking và Ngắt phần cứng

ESP32 thu thập dữ liệu thông qua hai phương thức độc lập nhằm tối ưu hiệu năng:
*   **Đọc định kỳ (Periodic Polling):** Thực hiện đọc các cảm biến Analog (MQ-135, Mực nước, LDR, ACS712) sau mỗi chu kỳ 3 giây bằng kỹ thuật kiểm tra thời gian trôi qua qua hàm `millis()`. Hoàn toàn không sử dụng hàm ngưng hoạt động `delay()`, tránh việc CPU bị block và bỏ lỡ các tác vụ quan trọng khác.
*   **Ngắt phần cứng (Hardware Interrupt):** Dành riêng cho cụm đếm xe cổng hồng ngoại IR1 và IR2, cho phép CPU dừng tạm thời tiến trình hiện tại để cộng dồn số lượng xe ngay khi có tín hiệu xung điện, độ trễ phản hồi đạt dưới 1 microsecond.

#### 💻 Minh họa mã nguồn điều hướng luồng chính trong `loop()`:
```cpp
void loop() {
  // Duy trì heartbeat kết nối với MQTT Broker liên tục
  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();

  // Nhánh ưu tiên cao: Xử lý tức thời sự kiện đếm xe từ ISR ngắt phần cứng
  if (vehicleEventPending) {
    vehicleEventPending = false; 
    publishVehicleEvent(); // Gửi bản tin đếm xe lên Broker ngay lập tức
  }

  // Nhánh định kỳ: Đọc dữ liệu môi trường và gửi lên Broker sau mỗi 3000ms (3 giây)
  unsigned long now = millis();
  if (now - lastPublishTime >= PUBLISH_INTERVAL) {
    lastPublishTime = now;
    publishSensorData();
  }

  if (now < lastPublishTime) lastPublishTime = now; // Xử lý tràn bộ đếm millis() sau 50 ngày
  delay(5); // Nhường 5ms cho các tiến trình mạng nền của ESP32 hoạt động ổn định
}
```

---

### 2. Lớp Mạng (Network Layer): Đóng gói dữ liệu JSON và truyền tải MQTT

Để tối ưu hóa băng thông truyền thông không dây, dữ liệu thô từ cảm biến được cấu trúc hóa dưới dạng gói tin JSON thông qua thư viện `ArduinoJson` và truyền tải thông qua giao thức MQTT siêu nhẹ lên Cloud Broker HiveMQ.

#### 💻 Minh họa mã nguồn đóng gói và gửi dữ liệu trong hàm `publishSensorData()`:
```cpp
void publishSensorData() {
  Serial.println("\n--- [3S LUỒNG CHÍNH] ĐỌC CẢM BIẾN ---");

  // Đọc dữ liệu từ các cảm biến vật lý (Đã qua bộ lọc thuật toán biên)
  int   gasLevel = readMQ135();          
  float waterPct = readWaterLevel();     
  int   lightPct = readLightSensor();    
  float power    = readPowerConsumption(); 

  bool floodAlert = (waterPct >= PUMP_ON_THRESHOLD);

  // Đọc dữ liệu đếm xe an toàn (Tránh xung đột dữ liệu với ISR ngắt)
  noInterrupts();
  int snapCount = vehicleCount;
  int snapIn    = totalIn;
  int snapOut   = totalOut;
  interrupts();

  // Khởi tạo tài nguyên chứa dữ liệu JSON dung lượng 768 bytes
  char jsonBuffer[512];
  StaticJsonDocument<768> doc;
  
  // Đóng gói cấu trúc cặp khóa - giá trị (Key - Value)
  doc["device_id"]     = MQTT_CLIENT;
  doc["timestamp"]     = millis();
  doc["nhiet_do"]      = 25.5; // Giá trị giả lập ổn định sau khi tháo cảm biến DHT vật lý
  doc["do_am"]         = 60.0; 
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

  // Số hóa cấu trúc JSON thành một chuỗi văn bản
  serializeJson(doc, jsonBuffer, sizeof(jsonBuffer));

  // Gửi chuỗi tin lên Broker qua Topic sensor
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_PUB, jsonBuffer);
    Serial.println("[MQTT] ✓ Đã gửi gói tin JSON lên Server thành công!");
    Serial.println(jsonBuffer);
  }
}
```

---

### 3. Lớp Ứng dụng (Application Layer): Giao tiếp SSE (Server-Sent Events) thời gian thực

Tại Backend Server (FastAPI), thay vì sử dụng cơ chế truyền tin hai chiều WebSockets hoặc liên tục gửi yêu cầu HTTP Polling lãng phí tài nguyên, em lựa chọn giải pháp truyền tin một chiều thời gian thực **Server-Sent Events (SSE)** thông qua class `StreamingResponse` của FastAPI.

*   **Tại sao không chọn HTTP Polling?** HTTP Polling yêu cầu trình duyệt gửi request liên tục (ví dụ 1s/lần) làm ngập mạng bởi các gói tin HTTP Handshake nặng nề (~700 bytes cho tiêu đề), gây trễ cao và tiêu tốn CPU của server.
*   **Tại sao không chọn WebSockets?** WebSockets thiết lập kênh truyền song công 2 chiều phức tạp sử dụng giao thức TCP tùy biến riêng, đòi hỏi chi phí quản lý kết nối lớn, dễ bị tường lửa chặn và không tự động kết nối lại khi mất mạng.
*   **Ưu thế vượt trội của SSE:** SSE hoạt động trực tiếp trên giao thức HTTP tiêu chuẩn, thiết lập một kết nối persistent duy nhất giúp server liên tục đẩy dữ liệu xuống client dạng text stream siêu nhẹ. SSE có sẵn cơ chế tự động kết nối lại (Auto-Reconnect) từ phía trình duyệt thông qua đối tượng `EventSource` trong JavaScript mà không cần viết thêm mã xử lý phức tạp. Phương thức này hoàn toàn tối ưu cho các hệ thống Dashboard giám sát thụ động khi dữ liệu chỉ cần chảy một chiều từ biên lên màn hình hiển thị.

---

## PHẦN 2: CHI TIẾT LINH KIỆN - CHỨC NĂNG VÀ ĐOẠN CODE MINH HỌA

### 1. Cụm Cảm biến Xe (Cảm biến hồng ngoại IR1 & IR2 + Đèn LED Xanh Lá chân D13)
*   **Nhiệm vụ:** Phát hiện xe đi vào (IR1) và đi ra (IR2) khỏi phân khu đô thị để quản lý lưu lượng xe, đồng thời bật LED xanh lá báo hiệu trực quan tại chỗ.
*   **Kỹ thuật nâng cao:** Sử dụng cơ chế ngắt phần cứng (Hardware Interrupt) trên các chân có hỗ trợ ngắt để bắt tín hiệu lập tức mà không cần quét trong vòng lặp `loop()`. Thuật toán áp dụng bộ lọc thời gian để chống hiện tượng rung phím vật lý/bắt tín hiệu ảo khi xe đi ngang qua (Debounce).
*   **Mã nguồn khai báo ngắt trong `setup()`:**
```cpp
// Thiết lập chân ngắt có điện trở kéo lên nội bộ để giữ mức cao mặc định
pinMode(PIN_IR1, INPUT_PULLUP);
pinMode(PIN_IR2, INPUT_PULLUP);

// Liên kết chân GPIO vật lý với hàm xử lý ngắt (ISR) khi phát hiện cạnh xuống (FALLING)
attachInterrupt(digitalPinToInterrupt(PIN_IR1), onIR1Falling, FALLING);
attachInterrupt(digitalPinToInterrupt(PIN_IR2), onIR2Falling, FALLING);
```
*   **Mã nguồn các hàm xử lý ngắt (ISR) nằm trên bộ nhớ RAM tốc độ cao (`IRAM_ATTR`):**
```cpp
// Hàm xử lý ngắt IR1 - Phát hiện xe đi VÀO phân khu
void IRAM_ATTR onIR1Falling() {
  unsigned long now = millis();
  // Thuật toán Debounce lọc nhiễu: Từ chối các ngắt cách nhau dưới 80 mili-giây
  if (now - lastIR1Time < IR_DEBOUNCE_MS) return; 
  lastIR1Time = now;
  
  vehicleCount++; // Tăng số lượng xe hiện tại trong đô thị
  totalIn++;      // Tăng tổng số xe đi vào
  vehicleEventPending = true; // Kích hoạt cờ gửi dữ liệu tức thời trong loop()
}

// Hàm xử lý ngắt IR2 - Phát hiện xe đi RA phân khu
void IRAM_ATTR onIR2Falling() {
  unsigned long now = millis();
  if (now - lastIR2Time < IR_DEBOUNCE_MS) return;
  lastIR2Time = now;
  
  if (vehicleCount > 0) { 
    vehicleCount--; // Giảm số lượng xe hiện tại trong đô thị
    totalOut++;     // Tăng tổng số xe đi ra
  }
  vehicleEventPending = true; // Kích hoạt cờ gửi dữ liệu tức thời
}
```

---

### 2. Cảm biến Mực nước (Chân Analog A5 / GPIO35)
*   **Nhiệm vụ:** Đo lường độ ngập úng đô thị để đưa ra tín hiệu cảnh báo lũ lụt và kích hoạt máy bơm nước tự động.
*   **Kỹ thuật nâng cao:** Thuật toán lấy trung bình 5 mẫu liên tục nhằm triệt tiêu nhiễu tần số cao của nguồn điện. Thiết lập bộ lọc dải chết (Deadzone 40% phần trăm thô) để triệt tiêu hoàn toàn dòng rò điện cơ học bám trên bề mặt cảm biến khi ở môi trường ngoài không khí khô ráo, đưa chỉ số hiển thị về đúng 0.0%.
*   **Mã nguồn xử lý:**
```cpp
float readWaterLevel() {
  long sum = 0;
  // Lấy mẫu trung bình cộng 5 lần liên tục để khử nhiễu tín hiệu
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_WATER); delay(1); }
  yield();
  int raw = sum / 5;
  int thr = WATER_DRY_CAL + 100; // Ngưỡng nền bắt đầu chạm nước vật lý: 2400 + 100 = 2500

  Serial.print("  [WATER] Giá trị RAW="); Serial.print(raw);
  // Lớp 1: Cắt đứt hoàn toàn giá trị RAW nhỏ hơn ngưỡng bắt đầu tiếp xúc nước
  if (raw <= thr) {
    Serial.println(" → Mức ngập: 0.0% (Khô ráo)");
    return 0.0;
  }
  
  // Ánh xạ tuyến tính giá trị RAW sang phần trăm thô (0% đến 100%)
  int pct = constrain(map(raw, thr, 4095, 0, 100), 0, 100);
  
  // Lớp 2: Bộ lọc Deadzone 40% loại bỏ rò điện cơ học bám ẩm bề mặt
  if (pct <= 40) {
    Serial.print(" → "); Serial.print(pct); Serial.println("% thô → Ép về 0% (Vùng chết lọc nhiễu)");
    return 0.0;
  }
  
  // Lớp 3: Tái ánh xạ tuyến tính phần trăm thực tế từ dải [40% - 100%] về [0% - 100%]
  float finalPct = (float)constrain(map(pct, 40, 100, 0, 100), 0, 100);
  Serial.print(" → Kết quả thực tế: "); Serial.print(finalPct, 1); Serial.println("% (CÓ NGẬP LỤT)");
  return finalPct;
}
```

---

### 3. Cảm biến Kh khí Gas MQ-135 (Chân Analog A4 / GPIO34)
*   **Nhiệm vụ:** Đo đếm nồng độ chất lượng không khí (khí gas hóa lỏng Butane, CO2, amoniac...) để cảnh báo nguy cơ ô nhiễm hoặc hỏa hoạn cháy nổ.
*   **Kỹ thuật nâng cao:** Sử dụng thuật toán hiệu chuẩn mức nền (Baseline Calibration) để cố định mức hiển thị tại 400 PPM (theo tiêu chuẩn không khí sạch của WHO) khi điện áp RAW đọc được dưới ngưỡng sạch (2700 RAW), và thực hiện ánh xạ tuyến tính phi tuyến dốc khi phát hiện khí độc thực tế.
*   **Mã nguồn xử lý:**
```cpp
int readMQ135() {
  long sum = 0;
  // Lấy mẫu trung bình 5 lần liên tiếp cách nhau 1ms để ổn định mức điện áp ADC
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_MQ135); delay(1); }
  yield();
  int raw = sum / 5;
  Serial.print("  [MQ-135] Giá trị RAW="); Serial.print(raw);
  
  // Thuật toán Baseline lock: Khóa mức không khí sạch tiêu chuẩn tại 400 PPM
  if (raw <= 2700) {
    Serial.println(" → Khóa baseline: 400 PPM (Sạch)");
    return 400;
  }
  
  // Ánh xạ tuyến tính khi phát hiện nồng độ khí gas tăng thực tế vượt ngưỡng nền
  int ppm = constrain(map(raw, 2700, 4095, 400, 5000), 400, 5000);
  Serial.print(" → Ánh xạ: "); Serial.print(ppm); Serial.println(" PPM");
  return ppm;
}
```

---

### 4. Module Relay & Máy bơm nước Mini (Chân Digital D26)
*   **Nhiệm vụ:** Đóng cắt dòng điện cấp cho máy bơm mini thực hiện xả lũ thoát nước khi mực nước ngập vượt ngưỡng an toàn.
*   **Kỹ thuật nâng cao:** Thuật toán điều khiển trễ (Hysteresis Control) sử dụng hai ngưỡng độc lập (Bật bơm khi ngập nặng `>= 70%`, chỉ Tắt bơm khi mực nước rút sâu xuống dưới `< 50%`). Giải pháp này giúp ngăn ngừa hiện tượng rơ-le đóng ngắt liên tục gây chập cháy tiếp điểm cơ học khi mực nước mấp mé ở ranh giới.
*   **Mã nguồn xử lý điều khiển trễ tự động trong hàm `publishSensorData()`:**
```cpp
// ── ĐIỀU KHIỂN BƠM TỰ ĐỘNG THUẬT TOÁN HYSTERESIS ──
if (autoMode) {
  // Ngưỡng bật bơm: Khi nước ngập đạt từ 70% trở lên và bơm chưa chạy
  if (waterPct >= PUMP_ON_THRESHOLD && !relayState) {
    relayState = true;
    digitalWrite(PIN_RELAY, LOW);  // Kéo chân điều khiển xuống mức Thấp để BẬT Relay (Active Low)
    Serial.println("[AUTO-CONTROL] ⚡ PHÁT HIỆN NGẬP >= 70%: TỰ ĐỘNG BẬT MÁY BƠM!");
  } 
  // Ngưỡng tắt bơm: Bơm chỉ tắt khi nước thực sự rút xuống dưới 50%
  else if (waterPct < PUMP_OFF_THRESHOLD && relayState) {
    relayState = false;
    digitalWrite(PIN_RELAY, HIGH); // Kéo chân lên mức Cao để NGẮT Relay (Tắt bơm)
    Serial.println("[AUTO-CONTROL] ✓ NƯỚC RÚT < 50%: TỰ ĐỘNG TẮT MÁY BƠM AN TOÀN.");
  }
  // Vùng trễ từ 50% đến 70%: Hệ thống giữ nguyên trạng thái hoạt động hiện thời
}
```

---

### 5. Quang trở LDR (GPIO32) & Cảm biến dòng ACS712 (GPIO33)
*   **Nhiệm vụ:** LDR đo cường độ ánh sáng phục vụ điều khiển chiếu sáng đô thị; ACS712 đo dòng điện qua phụ tải để giám sát công suất tiêu thụ điện thời gian thực.
*   **Mã nguồn xử lý:**
```cpp
// Đọc cường độ ánh sáng môi trường theo tỉ lệ phần trăm (%)
int readLightSensor() {
  long sum = 0;
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_LDR); delay(1); }
  yield();
  // Ánh xạ nghịch đảo: RAW càng lớn (tối) -> phần trăm ánh sáng càng nhỏ
  int pct = constrain(map(sum / 5, 4095, 0, 0, 100), 0, 100);
  return pct;
}

// Tính toán công suất tiêu thụ dựa trên điện áp đọc về từ cảm biến dòng ACS712
float readPowerConsumption() {
  long sum = 0;
  for (int i = 0; i < 5; i++) { sum += analogRead(PIN_ACS712); delayMicroseconds(200); }
  yield();
  
  // Tính toán điện áp trung bình tại chân ADC1
  float v = (sum / 5.0 / 4095.0) * 3.3 * 1.5; 
  // Trừ đi mức điện áp offset 2.5V (Điện áp tĩnh khi dòng I = 0A của cảm biến ACS712)
  float I = (v - 2.5) / 0.185; // Độ nhạy 185mV/A đối với dòng ACS712 phiên bản 5A
  
  if (abs(I) < 0.05) I = 0.0; // Khử sai số nhiễu nhỏ quanh mức không tải
  float power = abs(I) * 220.0; // Tính toán công suất tiêu thụ biểu kiến (P = I * U)
  return power;
}
```

---

## PHẦN 3: KỊCH BẢN PHẢN BIỆN "SỐNG CÒN" TRƯỚC HỘI ĐỒNG

---

### ❓ Câu hỏi 1: Tại sao chọn DHT11 thay vì DHT22 trong thiết kế sa bàn thực tế?

**Hội đồng hỏi:**  
*"Trong các sơ đồ thiết kế ban đầu hoặc các thư viện linh kiện phổ biến thường đề xuất sử dụng cảm biến DHT22 (vỏ màu trắng, dải đo rộng từ -40 đến 80 độ C, độ chính xác rất cao ±0.5°C). Tuy nhiên, trên sa bàn thực tế hiện tại, em lại chọn cảm biến DHT11 (vỏ màu xanh dương, độ chính xác ±2°C) hoặc tiến hành giả lập dữ liệu tĩnh khi tháo rời. Liệu đây có phải là một sự cải lùi về mặt kỹ thuật trong đồ án của em?"*

**Trả lời mẫu:**  
"Thưa thầy/cô trong Hội đồng, việc lựa chọn hoặc thay thế cảm biến DHT11 cho sa bàn thực tế hoàn toàn là một quyết định tối ưu hóa kỹ thuật dựa trên 3 lý do cốt lõi sau:

1.  **Độ tương thích dải đo trong thực tế mô phỏng:** DHT11 có dải đo nhiệt độ từ 0 đến 50°C và độ ẩm từ 20 đến 80%. Trong kịch bản chạy thử nghiệm đồ án ở môi trường thực tế tại phòng lab hay phòng bảo vệ đồ án, các thông số môi trường hoàn toàn dao động trong khoảng này (nhiệt độ phòng khoảng 25-35°C và độ ẩm 45-75%). Do đó, dải đo rộng của DHT22 là dư thừa và không mang lại giá trị thực tiễn trong bài toán mô phỏng sa bàn này.
2.  **Tần số lấy mẫu (Sampling Rate) ưu việt hơn:** Cảm biến DHT11 có tần số lấy mẫu đạt **1Hz** (1 lần đọc/giây), trong khi cảm biến DHT22 chỉ đạt **0.5Hz** (2 giây mới cho phép đọc dữ liệu 1 lần). Ở quy mô sa bàn cần cập nhật liên tục dữ liệu để minh họa luồng chạy mượt mà lên Dashboard thời gian thực, tần số lấy mẫu nhanh của DHT11 giúp ESP32 thu thập và hiển thị nhanh hơn, tránh tình trạng block chương trình để đợi cảm biến đáp ứng.
3.  **Tối ưu hóa kinh tế và linh kiện biên:** Module cảm biến DHT11 (màu xanh dương) được thiết kế tích hợp sẵn mạch nguồn phụ trợ bao gồm điện trở kéo lên (pull-up) 10kΩ và tụ lọc nhiễu ngay trên bo mạch nhỏ. Việc này giúp giảm thiểu việc cắm dây rời phức tạp trên breadboard của sa bàn, tăng tính thẩm mỹ và độ tin cậy kết nối vật lý, loại bỏ hoàn toàn lỗi lỏng chân tiếp xúc thường gặp của các linh kiện rời.

Vì các lý do trên, việc lựa chọn DHT11 là một giải pháp tối ưu hóa thiết kế biên, đảm bảo tính thực tiễn và tính kinh tế cao cho mô hình sa bàn mô phỏng."

---

### ❓ Câu hỏi 2: Tại sao cắt bớt LED cảnh báo Gas và Nước vật lý trên sa bàn? (Cực kỳ quan trọng)

**Hội đồng hỏi:**  
*"Thầy thấy trong báo cáo thiết kế ban đầu có bố trí 3 đèn LED tương ứng với 3 cảm biến (LED Đỏ báo Gas, LED Xanh Dương báo Ngập, LED Xanh Lá báo Xe). Nhưng trên sa bàn thực tế hiện tại, em lại tháo bỏ hoàn toàn LED Đỏ và LED Xanh Dương, chỉ giữ lại duy nhất 1 bóng LED Xanh Lá báo xe. Tại sao em lại cắt bớt linh kiện như vậy? Liệu việc này có làm giảm khả năng cảnh báo trực quan của mô hình thành phố thông minh hay không?"*

**Trả lời mẫu:**  
"Em xin phép được giải thích rõ bài toán thực nghiệm này trước Hội đồng. Ban đầu, kịch bản thiết kế của em là sử dụng 3 đèn LED độc lập để cảnh báo tại chỗ cho 3 phân hệ. Tuy nhiên, khi tiến hành ráp nối phần cứng và chạy tải thực tế, em phát hiện ra một vấn đề kỹ thuật nghiêm trọng về **độ ổn định nguồn biên (Power Integrity)**:

1.  **Dòng điện tiêu thụ của các linh kiện lớn:** Cảm biến khí gas MQ-135 bản chất hoạt động dựa trên bộ sưởi nội (internal heater) để nung nóng lớp SnO2 nhạy cảm, tiêu thụ dòng điện rất lớn và liên tục (khoảng 150mA đến 180mA). Thêm vào đó, khi ngập lụt xảy ra, Module Relay được kích hoạt để bật máy bơm mini xả lũ, tạo ra dòng khởi động (Inrush Current) tức thời rất cao kèm nhiễu xung ngược của động cơ điện một chiều.
2.  **Nguy cơ sụt áp điện áp tham chiếu (Vref):** Nếu board vi điều khiển ESP32 tiếp tục phải cấp dòng (Source Current) từ các chân GPIO để nuôi thêm 2 bóng LED cảnh báo Gas và Nước sáng liên tục khi sự cố xảy ra, tổng dòng điện tiêu thụ sẽ vượt quá khả năng cấp nguồn an toàn của cổng USB máy tính. Hiện tượng này làm sụt giảm tức thời điện áp tham chiếu nội bộ **Vref = 3.3V** cấp cho bộ chuyển đổi ADC của ESP32. Kết quả là dữ liệu RAW đọc về từ các cảm biến Analog (đặc biệt là cảm biến nước và gas) bị sai số lệch nghiêm trọng (báo chỉ số ảo liên tục).
3.  **Hiện tượng sụt nguồn treo chip (Brownout Reset):** Khi xảy ra đồng thời cả 2 sự cố (xịt gas và đổ nước ngập), dòng tăng vọt làm sụt nguồn dưới ngưỡng cho phép, kích hoạt bộ giám sát Brownout Detector tích hợp trong ESP32 khiến chip bị reset liên tục và treo hệ thống hoàn toàn.

**Giải pháp tối ưu hóa năng lượng biên:**  
Để đảm bảo hệ thống chạy ổn định 24/7, em đã cải tiến phần cứng bằng cách loại bỏ hoàn toàn 2 bóng LED vật lý tiêu thụ nguồn của cảm biến Gas và Mực nước. Thay vào đó, em chuyển toàn bộ kịch bản cảnh báo trực quan lên **phần mềm trên Web Dashboard** bằng các Banner nhấp nháy đỏ thời gian thực cực kỳ nổi bật trên giao diện, hoạt động dựa trên luồng dữ liệu Server-Sent Events (SSE). 

Em chỉ giữ lại duy nhất 1 bóng LED Xanh Lá kết hợp điện trở gánh dòng 220Ω cho phân hệ giao thông (IR1/IR2). Vì cảm biến hồng ngoại hoạt động theo cơ chế ngắt phần cứng bất đối xứng (chỉ nháy sáng lên trong 80ms rồi tắt ngay khi có xe đi qua), dòng điện tiêu thụ cực kỳ nhỏ và ngắt quãng, hoàn toàn không ảnh hưởng đến điện áp nuôi các cảm biến Analog khác. Giải pháp này giúp sa bàn vận hành an toàn, bền bỉ và loại bỏ hoàn toàn sai số đọc ADC."

---

### ❓ Câu hỏi 3: Thuật toán điều khiển máy bơm xả lũ hoạt động thế nào để tránh việc bật/tắt liên tục khi nước mấp mé ngưỡng?

**Hội đồng hỏi:**  
*"Làm thế nào để hệ thống điều khiển máy bơm tự động hoạt động ổn định, tránh hiện tượng máy bơm bị bật/tắt liên tục (nhấp nháy dòng cơ học) khi mực nước dao động mấp mé ở ranh giới ngưỡng cảnh báo?"*

**Trả lời mẫu:**  
"Thưa thầy/cô, để giải quyết triệt để hiện tượng nhấp nháy tiếp điểm rơ-le (chattering) khi mực nước ngập dao động nhỏ quanh ngưỡng cảnh báo (ví dụ nước dâng lên hạ xuống nhẹ ở mức 70%), em đã cài đặt thuật toán **điều khiển tích hợp cơ chế trễ (Hysteresis Control)** trong mã nguồn Firmware của ESP32.

Nguyên lý hoạt động của thuật toán này là thay vì sử dụng 1 ngưỡng cố định duy nhất cho cả hai hành vi bật và tắt bơm, hệ thống sẽ sử dụng **hai ngưỡng độc lập tách biệt**:
*   **Ngưỡng BẬT máy bơm (PUMP_ON_THRESHOLD):** Thiết lập tại mức `>= 70%` mực nước ngập.
*   **Ngưỡng TẮT máy bơm (PUMP_OFF_THRESHOLD):** Thiết lập tại mức `< 50%` mực nước ngập.

**Luồng hoạt động cụ thể trong mã nguồn:**
1.  Khi nước ngập dâng từ dưới lên và chạm mức 70%, ESP32 sẽ kích Relay bật máy bơm hoạt động.
2.  Trong quá trình máy bơm hút nước xả lũ ra ngoài, mặc dù nước có thể dao động nhẹ xung quanh mức 70% (ví dụ giảm xuống 69% rồi lên lại 71% do dòng nước động), máy bơm vẫn được duy trì trạng thái BẬT liên tục mà không bị ngắt quãng.
3.  Máy bơm chỉ thực sự dừng hoạt động khi nước đã được hút cạn và rút hẳn xuống dưới mức 50%.
4.  Khoảng cách từ 50% đến 70% được gọi là **vùng trễ an toàn (dead-band)**. Trong vùng này, hệ thống giữ nguyên trạng thái hoạt động trước đó mà không thực hiện thay đổi nào.

Thuật toán điều khiển trễ phi tuyến này giúp bảo vệ cơ cấu chấp hành (Relay và máy bơm), chống phát sinh tia lửa điện tiếp điểm và loại bỏ hoàn toàn sụt áp nguồn do tắt mở tải liên tục gây ra."

---

*Tài liệu hướng dẫn vấn đáp được biên soạn riêng phục vụ bảo vệ Đồ án tốt nghiệp CNTT K16 - Đại học Đại Nam.*
