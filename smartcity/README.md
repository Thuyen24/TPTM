# 🏙️ Smart City Dashboard — Hướng Dẫn Triển Khai Hoàn Chỉnh
> **Đề tài**: Bảng Điều Khiển Trung Tâm Cho Thành Phố Thông Minh  
> **Stack**: ESP32 (C++) → HiveMQ MQTT → FastAPI + SQLite → HTML Dashboard

---

## 📁 Cấu trúc thư mục dự án

```
smartcity/
├── BUOC_1_2_KIEN_TRUC_VA_PHANCUNG.md   ← Kiến trúc + Sơ đồ đấu nối
├── BUOC_3_ESP32_firmware.ino            ← Code nạp vào ESP32
├── BUOC_4_main.py                       ← Backend FastAPI
├── BUOC_4_requirements.txt              ← Thư viện Python
├── BUOC_5_index.html                    ← Dashboard Web
└── README.md                            ← File này
```

---

## ✅ BƯỚC 1 — Kiến trúc hệ thống

**Luồng dữ liệu 4 tầng:**

```
[Cảm biến] → ESP32 (C++) → HiveMQ MQTT → FastAPI (Python) → Dashboard (HTML/JS)
                  ↑                              ↓
            [Relay/LED]          ←←← smartcity/control ←←← Nút bấm Dashboard
```

**File tham khảo:** `BUOC_1_2_KIEN_TRUC_VA_PHANCUNG.md`

---

## ✅ BƯỚC 2 — Sơ đồ đấu nối phần cứng

### Bảng GPIO tóm tắt

| GPIO | Linh kiện | Loại | Nguồn |
|------|-----------|------|-------|
| 4 | DHT22 DATA | Digital I/O | ESP32 3V3 |
| 18 | IR Sensor #1 (xe vào) | Digital IN | 5V MB102 |
| 19 | IR Sensor #2 (xe ra) | Digital IN | 5V MB102 |
| 25 | LED Đỏ cảnh báo | Digital OUT | — |
| 26 | Relay IN | Digital OUT | 5V MB102 |
| 27 | LED Xanh | Digital OUT | — |
| 32 | LDR (ánh sáng) | ADC IN | ESP32 3V3 |
| 33 | ACS712 (dòng điện) | ADC IN | **5V MB102** |
| 34 | MQ-135 (khí gas) | ADC IN | **5V MB102** |
| 35 | Water Level (mực nước) | ADC IN | ESP32 3V3 |

> ⚠️ MQ-135, ACS712, Relay, IR sensors: **VCC phải lấy từ dải ĐỎ (5V) của MB102**, KHÔNG từ ESP32!

**File tham khảo:** `BUOC_1_2_KIEN_TRUC_VA_PHANCUNG.md` (xem sơ đồ chi tiết)

---

## ✅ BƯỚC 3 — Nạp firmware ESP32

### Chuẩn bị Arduino IDE

1. Cài **Arduino IDE 2.x** từ https://www.arduino.cc
2. Vào `File → Preferences → Additional boards URL`, thêm:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Vào `Tools → Board Manager`, tìm **esp32**, cài phiên bản mới nhất
4. Vào `Tools → Manage Libraries`, cài:
   - **PubSubClient** (Nick O'Leary) — v2.8+
   - **DHT sensor library** (Adafruit) — v1.4+
   - **ArduinoJson** (Benoit Blanchon) — v6.x

### Chỉnh sửa trước khi nạp

Mở `BUOC_3_ESP32_firmware.ino`, sửa 2 dòng:
```cpp
const char* WIFI_SSID     = "TEN_WIFI_CUA_BAN";   // ← sửa tên WiFi
const char* WIFI_PASSWORD = "MAT_KHAU_WIFI";        // ← sửa mật khẩu
```

### Nạp code
1. `Tools → Board → ESP32 Dev Module`
2. `Tools → Port` → chọn cổng COM của ESP32
3. Nhấn **Upload** (Ctrl+U)
4. Mở **Serial Monitor** (115200 baud) để xem log

### Kiểm tra Serial Monitor
```
========================================
  SMART CITY — ESP32 Firmware v1.0
========================================
[WiFi] Đang kết nối: TenWifi...
[WiFi] Đã kết nối — IP: 192.168.1.x
[MQTT] Kết nối HiveMQ thành công!
[MQTT] Đã subscribe: smartcity/control
[MQTT] Đã gửi → {"device_id":"SmartCity_ESP32_001","nhiet_do":28.5,...}
```

---

## ✅ BƯỚC 4 — Khởi động Backend FastAPI

### Yêu cầu hệ thống
- Python 3.9+
- Kết nối Internet (để kết nối HiveMQ)

### Cài đặt và chạy

```bash
# Bước 1: Tạo thư mục và copy file
mkdir smartcity_backend
cd smartcity_backend
# Copy BUOC_4_main.py → main.py
# Copy BUOC_4_requirements.txt → requirements.txt
# Copy BUOC_5_index.html → index.html

# Bước 2: Tạo môi trường ảo (khuyến nghị)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Bước 3: Cài thư viện
pip install -r requirements.txt

# Bước 4: Chạy server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Kiểm tra backend đang chạy
```
INFO: Started server process
INFO: Waiting for application startup.
INFO: [DB] Khởi tạo SQLite thành công: smartcity.db
INFO: [MQTT] Đang kết nối broker.hivemq.com:1883 ...
INFO: [MQTT] Kết nối HiveMQ thành công!
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### API Endpoints

| Method | URL | Mô tả |
|--------|-----|-------|
| GET | `/` | Dashboard HTML |
| GET | `/api/data/latest` | Bản ghi cảm biến mới nhất |
| GET | `/api/data/history` | 20 bản ghi gần nhất |
| POST | `/api/control` | Gửi lệnh ON/OFF Relay |
| GET | `/api/status` | Trạng thái hệ thống |
| GET | `/docs` | Swagger UI tự động |

### Ví dụ test API

```bash
# Lấy dữ liệu mới nhất
curl http://localhost:8000/api/data/latest

# Bật Relay
curl -X POST http://localhost:8000/api/control \
     -H "Content-Type: application/json" \
     -d '{"command": "ON"}'

# Tắt Relay
curl -X POST http://localhost:8000/api/control \
     -H "Content-Type: application/json" \
     -d '{"command": "OFF"}'
```

---

## ✅ BƯỚC 5 — Mở Dashboard

Sau khi backend đang chạy, truy cập:

```
http://localhost:8000
```

Hoặc nếu chạy trên PC khác trong mạng LAN:
```
http://192.168.1.xxx:8000   ← IP của máy chạy backend
```

> **Lưu ý**: Nếu mở trực tiếp file `index.html` từ trình duyệt (file://...) sẽ bị lỗi CORS.  
> Phải mở qua URL của backend (`http://localhost:8000`) hoặc cấu hình CORS trong FastAPI.

### Giao diện Dashboard bao gồm

| Thành phần | Mô tả |
|-----------|-------|
| 🔴 **Banner cảnh báo ngập lụt** | Chớp nháy đỏ khi `ngap_lut: true` |
| 🌡️ **Card Nhiệt độ** | Số lớn + progress bar (max 60°C) |
| 💧 **Card Độ ẩm** | Số lớn + progress bar (0–100%) |
| 🚗 **Card Tổng số xe** | Đếm xe real-time |
| ⚡ **Card Công suất** | Watt từ ACS712 |
| 📈 **Biểu đồ Khí gas** | Chart.js đường, 20 điểm real-time |
| 📈 **Biểu đồ Lưu lượng xe** | Chart.js đường, 20 điểm real-time |
| 💡 **Mực nước + Ánh sáng** | Progress bar có ngưỡng 70% |
| 🔌 **Nút Bật/Tắt Relay** | Gọi API POST → MQTT → ESP32 |

---

## 🔁 Luồng hoạt động hoàn chỉnh

```
1. ESP32 đọc cảm biến mỗi 2 giây
   ↓
2. Đóng gói JSON:
   {"nhiet_do":28.5, "do_am":65.2, "chat_luong_kk":1250,
    "so_xe":3, "muc_nuoc":45.0, "anh_sang":78, "cong_suat":220.0,
    "ngap_lut":false, "device_id":"SmartCity_ESP32_001"}
   ↓
3. Publish lên HiveMQ topic: smartcity/sensors
   ↓
4. FastAPI nhận qua paho-mqtt (thread riêng)
   ↓
5. Lưu vào SQLite: file smartcity.db
   ↓
6. Dashboard gọi GET /api/data/latest mỗi 2 giây
   ↓
7. Cập nhật Cards + Charts trên trình duyệt
   ↓
8. Người dùng bấm nút "BẬT" trên Dashboard
   ↓
9. Dashboard gọi POST /api/control {"command":"ON"}
   ↓
10. FastAPI publish "ON" lên topic: smartcity/control
    ↓
11. ESP32 nhận qua callback → digitalWrite(PIN_RELAY, LOW) → Relay BẬT
```

---

## 🐛 Xử lý sự cố thường gặp

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| ESP32 không kết nối WiFi | Sai SSID/Pass | Kiểm tra Serial Monitor, sửa firmware |
| ESP32 không gửi MQTT | Broker bận hoặc mạng yếu | Thử lại, HiveMQ public đôi khi tải cao |
| Dashboard không cập nhật | Backend chưa chạy | Mở terminal, kiểm tra `uvicorn` |
| DHT22 trả về nan | Dây nối lỏng, thiếu pull-up | Kiểm tra điện trở 10kΩ, dây DATA |
| ADC đọc nhảy loạn | Thiếu tụ lọc hoặc nguồn nhiễu | Thêm tụ 100nF giữa VCC và GND của cảm biến |
| Relay không tắt khi khởi động | Quên `digitalWrite(26, HIGH)` trong setup | Kiểm tra lại code setup() |
| ACS712 ra giá trị lạ | Cầu phân áp sai | Kiểm tra R1=10kΩ, R2=20kΩ |

---

## 📌 Lưu ý quan trọng cho báo cáo

1. **HiveMQ Public Broker** là MQTT broker miễn phí, không cần tài khoản, nhưng không mã hóa (TLS). Phù hợp cho demo/học tập.
2. **SQLite cục bộ** — không cần server DB, file `smartcity.db` tự động tạo khi chạy backend.
3. **Relay LOW level trigger**: luôn khởi tạo `HIGH` trong `setup()` để tránh relay tự BẬT khi mới cấp nguồn.
4. **ESP32 ADC**: GPIO 34–39 chỉ là Input, không thể dùng làm Output. ADC của ESP32 có thể không tuyến tính hoàn toàn — cần hiệu chỉnh nếu cần độ chính xác cao.
5. Dashboard tự động **polling mỗi 2 giây**, không dùng WebSocket (đơn giản hơn, phù hợp demo).
