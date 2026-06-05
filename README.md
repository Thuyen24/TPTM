
<div align="center">

# 🏙️ Smart City Central Dashboard
### Bảng Điều Khiển Trung Tâm Cho Thành Phố Thông Minh

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino_IDE-E7352C?style=for-the-badge&logo=espressif&logoColor=white)](https://espressif.com)
[![MQTT](https://img.shields.io/badge/MQTT-HiveMQ-660066?style=for-the-badge&logo=mqtt&logoColor=white)](https://www.hivemq.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

> **smartcity** · Đại học Đại Nam · Khoa Công nghệ Thông tin · 2026

</div>

---

## 📌 Giới Thiệu Tổng Quan

**Smart City Central Dashboard** là hệ thống giám sát và điều khiển đô thị thông minh thu nhỏ, được xây dựng trên nền tảng IoT 3 lớp. Dự án tích hợp sa bàn vật lý (tấm xốp phẳng, đi dây ngầm vuông góc) với hệ thống phần mềm giám sát thời gian thực qua giao thức MQTT và giao diện Web Dashboard hiện đại.

### 🎯 Tính Năng Nổi Bật

| Tính năng | Chi tiết |
|-----------|----------|
| 🌫️ **Giám sát chất lượng không khí** | Cảm biến MQ-135, hiệu chuẩn Baseline 2700 RAW → 400 PPM |
| 🌡️ **Nhiệt độ & Độ ẩm** | Module DHT11 xanh dương (tích hợp pull-up) |
| 🚗 **Đếm xe tự động** | Cặp cảm biến IR1/IR2 dùng Hardware Interrupt ISR (<1ms) |
| 🌊 **Giám sát ngập lụt** | Cảm biến mực nước + lọc nhiễu Deadzone 40% |
| 💡 **Quản lý điện năng** | Quang trở LDR + cảm biến dòng ACS712 |
| 🚨 **Cảnh báo kép** | LED vật lý (Đỏ/Xanh dương/Xanh lá) + Banner Web đỏ |
| 💧 **Bơm xả lũ tự động** | Relay Hysteresis: bật 70% / tắt 50% |
| 🕐 **Đồng hồ múi giờ VN** | `toLocaleTimeString('vi-VN')` chuẩn UTC+7 |

---

## 📁 Cấu Trúc Thư Mục

```
smartcity_dashboard/
│
├── 📂 smartcity/                              # Mã nguồn hệ thống chính
│   │
│   ├── 📂 BUOC_3_ESP32_firmware/             # Firmware vi điều khiển
│   │   └── BUOC_3_ESP32_firmware.ino         # Mã nguồn C++ nạp vào ESP32
│   │
│   ├── main.py                               # Backend: FastAPI Server + MQTT
│   ├── index.html                            # Frontend: Web Dashboard
│   ├── BUOC_4_requirements.txt              # Danh sách thư viện Python
│   ├── smartcity.db                          # CSDL SQLite (tự tạo khi chạy)
│   │
│   ├── BUOC_1_2_KIEN_TRUC_VA_PHANCUNG.md   # Tài liệu kiến trúc phần cứng
│   ├── MO_TA_LUONG_HOAT_DONG.md            # Mô tả luồng hoạt động hệ thống
│   ├── HUONG_DAN_NAP_CODE_ESP32.md         # Hướng dẫn nạp code lên ESP32
│   └── HUONG_DAN_CAI_THU_VIEN_VA_NAP_CODE.md
└── README.md                                 # ← File này
```

---

## 🔌 Sơ Đồ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────┐
│                    SA BÀN XỐP TRẮNG                      │
│                                                           │
│  [IR1-Cổng vào] ──┐    [MQ-135]   [DHT11]  [LDR]        │
│  [IR2-Cổng ra]  ──┤    [ACS712]   [Nước-Chai nhựa]       │
│                   ↓                                       │
│           ┌──────────────────┐                            │
│           │   ESP32 Dev      │  ← Firmware C++ v4.0      │
│           │   Module 30 chân │                            │
│           └──────────────────┘                            │
│  [LED ĐỎ-D2] [LED XANH-D4] [LED LÁ-D13] [Relay-D26]    │
└──────────────────────↕──────────────────────────────────┘
                       │ WiFi 2.4 GHz
                       ↓
              ┌─────────────────┐
              │  HiveMQ Broker  │  broker.hivemq.com:1883
              │  (MQTT Cloud)   │  Topic: smartcity/sensors
              └────────┬────────┘
                       │ TCP/IP
                       ↓
           ┌──────────────────────┐
           │  FastAPI Backend     │  http://localhost:8000
           │  Python + paho-mqtt  │  ← main.py
           │  SQLite: smartcity.db│
           └──────────┬───────────┘
                      │ REST API + SSE
                      ↓
           ┌──────────────────────┐
           │   Web Dashboard      │  Trình duyệt
           │   HTML/JS/Chart.js   │  ← index.html
           │   Cập nhật: 2s/lần   │
           └──────────────────────┘
```

---

## 🔧 Bảng Chân GPIO ESP32

| Chân | Tên Biến | Chế Độ | Loại Tín Hiệu | Thiết Bị | Vị Trí Sa Bàn |
|------|----------|--------|---------------|----------|----------------|
| **D2** | PIN_LED_RED | OUTPUT | Digital | LED Đỏ + R220Ω → Cảnh báo Gas | Cạnh bo mạch |
| **D4** | PIN_LED_BLUE | OUTPUT | Digital | LED Xanh Dương + R220Ω → Cảnh báo Ngập | Cạnh bo mạch |
| **D13** | PIN_LED_GREEN | OUTPUT | Digital | LED Xanh Lá + R220Ω → Báo xe qua | Cạnh bo mạch |
| **D18** | PIN_IR1 | INPUT_PULLUP | Digital/Ngắt | Hồng ngoại IR1 — Xe **VÀO** | Góc dưới TRÁI |
| **D19** | PIN_IR2 | INPUT_PULLUP | Digital/Ngắt | Hồng ngoại IR2 — Xe **RA** | Góc dưới PHẢI |
| **D26** | PIN_RELAY | OUTPUT | Digital | Module Relay (LOW = BẬT) — Máy bơm | Cạnh bo mạch |
| **D32** | PIN_LDR | INPUT | Analog ADC1 | Quang trở LDR đo ánh sáng | Mặt sa bàn |
| **D33** | PIN_ACS712 | INPUT | Analog ADC1 | Cảm biến dòng ACS712 | Nối tiếp phụ tải |
| **D34** | PIN_MQ135 | INPUT ONLY | Analog ADC1 | Cảm biến khí MQ-135 | Góc trên TRÁI |
| **D35** | PIN_WATER | INPUT ONLY | Analog ADC1 | Cảm biến mực nước | Góc dưới PHẢI |

> ⚠️ **Quan trọng**: D34 và D35 là **INPUT ONLY** — không có điện trở kéo nội. Tất cả cảm biến Analog dùng **ADC1** (D32–D39) để tránh xung đột WiFi (ADC2 bị vô hiệu khi WiFi bật).

---

## 💡 Logic 3 Đèn LED Cảnh Báo Vật Lý

```
LED ĐỎ   (D2)  → Bật khi Gas ≥ 2000 PPM       | Cảnh báo rò rỉ khí độc
LED XANH (D4)  → Bật khi Mực nước ≥ 70%        | Cảnh báo ngập lụt
LED LÁ   (D13) → Nhấp nháy 80ms mỗi xe qua     | Xác nhận phát hiện phương tiện

Khởi động (LED Self-Test): ĐỎ → XANH DƯƠNG → XANH LÁ (400ms mỗi bóng)
```

---

## ⚙️ Thuật Toán Xử Lý Tín Hiệu Biên

### 1. Lọc Nhiễu Mực Nước — Deadzone 40%

```cpp
// Lớp 1: Cắt baseline rò điện
if (raw <= 2500) return 0.0;          // → KHÔ tuyệt đối

// Lớp 2: Deadzone 40% chống dao động ẩm
int pct = map(raw, 2500, 4095, 0, 100);
if (pct <= 40) return 0.0;            // → Vẫn KHÔ

// Lớp 3: Remap tuyến tính 0%→100% thực tế
return map(pct, 40, 100, 0, 100);
```

### 2. Hiệu Chuẩn Baseline MQ-135

```cpp
if (raw <= 2700) return 400;                    // → Không khí sạch: 400 PPM
return constrain(map(raw, 2700, 4095, 400, 5000), 400, 5000);
```

### 3. Điều Khiển Bơm Hysteresis

```cpp
if (waterPct >= 70.0) pumpState = true;   // BẬT bơm khi ngập >= 70%
if (waterPct <  50.0) pumpState = false;  // TẮT bơm khi rút < 50%
// Vùng 50%–70%: giữ nguyên trạng thái (chống rung tiếp điểm Relay)
```

---

## 🛠️ Hướng Dẫn Cài Đặt và Chạy

### Yêu Cầu Hệ Thống

| Phần mềm | Phiên bản tối thiểu | Ghi chú |
|----------|---------------------|---------|
| Python | 3.10+ | [Tải tại python.org](https://python.org) |
| Arduino IDE | 2.x | [Tải tại arduino.cc](https://arduino.cc) |
| ESP32 Board Package | 2.x | Cài qua Board Manager |
| Trình duyệt | Chrome / Edge / Firefox | Bất kỳ trình duyệt hiện đại |

---

### 📦 Bước 1 — Cài Đặt Thư Viện Python (Backend)

```bash
# Di chuyển vào thư mục dự án
cd d:\DAIHOCDAINAM\THONGMINH\smartcity_dashboard\smartcity

# Tạo môi trường ảo (chỉ cần làm 1 lần)
python -m venv venv

# Kích hoạt môi trường ảo
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# Cài toàn bộ thư viện cần thiết
pip install -r BUOC_4_requirements.txt
```

**Danh sách thư viện sẽ được cài:**

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|----------|
| `fastapi` | 0.111.0 | Framework Web API hiệu năng cao |
| `uvicorn[standard]` | 0.29.0 | ASGI Server chạy FastAPI |
| `paho-mqtt` | 1.6.1 | MQTT Client kết nối HiveMQ Broker |
| `pydantic` | 2.7.1 | Validate dữ liệu tự động |

---

### 📡 Bước 2 — Cài Thư Viện Arduino và Nạp Firmware ESP32

#### 2.1. Thêm ESP32 Board Package vào Arduino IDE

```
File → Preferences → Additional Board Manager URLs:
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

```
Tools → Board → Boards Manager → Tìm "esp32" → Install
```

#### 2.2. Cài Thư Viện Arduino

Vào **Tools → Manage Libraries** và cài các thư viện sau:

| Thư viện | Tác giả | Phiên bản |
|----------|---------|-----------|
| **PubSubClient** | Nick O'Leary | v2.8+ |
| **ArduinoJson** | Benoit Blanchon | v6.x |

#### 2.3. Cấu Hình và Nạp Firmware

```
1. Mở file: smartcity/BUOC_3_ESP32_firmware/BUOC_3_ESP32_firmware.ino
2. Tìm dòng và sửa thông tin WiFi của bạn:
      const char* WIFI_SSID = "TÊN_WIFI_CỦA_BẠN";
      const char* WIFI_PASS = "MẬT_KHẨU_WIFI";
3. Chọn Board: Tools → Board → ESP32 Dev Module
4. Chọn Port: Tools → Port → COMxx (cổng ESP32 của bạn)
5. Nhấn Upload (→) và chờ hoàn thành
6. Mở Serial Monitor (115200 baud) để xem log kết nối
7. Quan sát LED Self-Test: ĐỎ → XANH DƯƠNG → XANH LÁ ✅
```

---

### 🚀 Bước 3 — Khởi Động Backend Server

```bash
# Từ thư mục smartcity/
.\venv\Scripts\python.exe main.py
```

✅ Dấu hiệu khởi động thành công:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started server process [xxxxx]
INFO:     Application startup complete.
[INFO] [DB] Khởi tạo SQLite thành công: smartcity.db
[INFO] [App] MQTT thread đã khởi động
```

---

### 🌐 Bước 4 — Mở Giao Diện Dashboard

```
Mở trình duyệt → Truy cập: http://localhost:8000
```

---

### ❗ Xử Lý Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `ModuleNotFoundError` | Chưa cài thư viện | Chạy lại `pip install -r BUOC_4_requirements.txt` |
| `Address already in use` | Cổng 8000 bị chiếm | `netstat -ano \| findstr :8000` → `taskkill /PID xxx /F` |
| ESP32 không kết nối WiFi | Sai tên/mật khẩu | Kiểm tra lại `WIFI_SSID` và `WIFI_PASS` trong file .ino |
| Dashboard không có dữ liệu | ESP32 chưa kết nối | Xem Serial Monitor, đảm bảo log MQTT Connected |
| `pip` không nhận lệnh | Chưa kích hoạt venv | Chạy `.\venv\Scripts\Activate.ps1` trước |

---

## 📊 API Endpoints

| Method | Endpoint | Mô Tả |
|--------|----------|-------|
| `GET` | `/` | Giao diện Dashboard chính (index.html) |
| `GET` | `/api/data/latest` | Dữ liệu cảm biến mới nhất |
| `GET` | `/api/data/history` | 20 bản ghi gần nhất (vẽ biểu đồ) |
| `POST` | `/api/control` | Gửi lệnh điều khiển xuống ESP32 |
| `GET` | `/api/status` | Trạng thái MQTT và Database |
| `GET` | `/docs` | Swagger UI — thử API trực tiếp |

---

## ✅ Danh Sách Tính Năng Đã Hoàn Thiện

- [x] Firmware ESP32 C++ với Hardware Interrupt ISR (<1ms) đếm xe
- [x] Lọc nhiễu 3 lớp cảm biến mực nước (Deadzone 40%)
- [x] Hiệu chuẩn mức nền MQ-135 (Baseline Lock 2700 RAW → 400 PPM)
- [x] Điều khiển bơm tự động Hysteresis (70% BẬT / 50% TẮT)
- [x] 3 đèn LED vật lý cảnh báo trên sa bàn xốp (D2, D4, D13)
- [x] Banner cảnh báo Web màu đỏ khi Gas ≥ 2000 PPM hoặc nước ≥ 70%
- [x] Đồng bộ múi giờ Việt Nam UTC+7 qua `toLocaleTimeString('vi-VN')`
- [x] REST API FastAPI + SQLite lưu lịch sử
- [x] Biểu đồ Chart.js thời gian thực (20 điểm gần nhất)
- [x] Swagger UI tự động tại `/docs`

---

## 📚 Tài Liệu Tham Khảo

- [Espressif ESP32 Technical Reference Manual](https://www.espressif.com/sites/default/files/documentation/esp32_technical_reference_manual_en.pdf)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com)
- [PubSubClient MQTT Library](https://pubsubclient.knolleary.net)
- [HiveMQ Public Broker](https://www.hivemq.com/public-mqtt-broker/)
- Nghị định số 30/2020/NĐ-CP ngày 05/3/2020 của Chính phủ về công tác văn thư

---

<div align="center">

## 👨‍💻 Tác Giả

<table>
  <tr>
    <td align="center">
      <b>Đỗ Văn Thuyên</b><br/>
      <sub>Mã số sinh viên: <b>1671020308</b></sub><br/>
      <sub>Sinh viên K16 — Ngành Công nghệ Thông tin</sub><br/>
      <sub>Khoa Công nghệ Thông tin — Đại học Đại Nam</sub><br/>
      <sub>📅 Năm tốt nghiệp: <b>2026</b></sub>
    </td>
  </tr>
</table>

---

*© 2026 · Đỗ Văn Thuyên · Đại học Đại Nam · Khoa Công nghệ Thông tin*

**"Xây dựng đô thị thông minh bắt đầu từ việc lắng nghe dữ liệu."**

</div>
