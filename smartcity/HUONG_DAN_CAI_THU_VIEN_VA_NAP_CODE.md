# 🔧 HƯỚNG DẪN: Cài Thư Viện + Kiểm Tra Chân + Nạp Code ESP32

> Dành cho sa bàn thực tế đã cắm xong phần cứng

---

## ✅ KIỂM TRA CHÂN GPIO: CODE vs SA BÀN THỰC TẾ

### Bảng so sánh:

| Cảm biến | Chân bạn cắm | Chân trong code | Khớp? | Ghi chú |
|----------|:------------:|:--------------:|:-----:|---------|
| DHT11 (nhiệt độ/ẩm) | **D4** | `PIN_DHT22 = 4` | ✅ | Chân khớp. Nhưng **loại cảm biến** khác: bạn dùng **DHT11** (xanh dương), code cũ ghi DHT22 → **đã sửa** thành `DHT11` |
| IR sensor 1 (xe vào) | **D18** | `PIN_IR1 = 18` | ✅ | Khớp hoàn toàn |
| IR sensor 2 (xe ra) | **D19** | `PIN_IR2 = 19` | ✅ | Khớp hoàn toàn |
| Relay | **D26** | `PIN_RELAY = 26` | ✅ | Khớp hoàn toàn |
| Mực nước | **D35** | `PIN_WATER = 35` | ✅ | Khớp, nguồn 3V3 đúng |
| MQ-2 (khói/gas) | **D34** | `PIN_MQ135 = 34` | ✅ | Chân khớp. Bạn dùng MQ-2 thay MQ-135, cùng đọc analog → OK |
| LDR (ánh sáng) | AO→**D32** | `PIN_LDR = 32` | ✅ | Code dùng chân AO (analog). Chân DO (D13) không dùng trong code |
| Module công suất | **D27** | `PIN_ACS712 = 33` | ⚠️ | **KHÔNG KHỚP** — xem giải thích bên dưới |

### ⚠️ VẤN ĐỀ VỚI MODULE CÔNG SUẤT (D27):

```
Bạn cắm module công suất vào D27
Nhưng D27 thuộc nhóm ADC2 của ESP32

╔══════════════════════════════════════════════════════╗
║  ESP32 CÓ 2 BỘ ADC:                                 ║
║                                                       ║
║  ADC1 (GPIO 32-39): LUÔN HOẠT ĐỘNG ✅               ║
║  ADC2 (GPIO 0-27):  TẮT KHI WiFi BẬT ❌            ║
║                                                       ║
║  → D27 = ADC2 → KHÔNG ĐỌC ĐƯỢC analog khi có WiFi  ║
║  → D33 = ADC1 → LUÔN ĐỌC ĐƯỢC ✅                   ║
╚══════════════════════════════════════════════════════╝
```

### 👉 BẠN CẦN ĐỔI 1 DÂY DUY NHẤT:

```
Rút dây OUT của module công suất từ  D27
                                      ↓
Cắm sang chân                       D33
```

> Chỉ rút 1 dây tín hiệu (OUT), giữ nguyên dây VCC và GND.
> Sau khi đổi, code sẽ dùng `PIN_ACS712 = 33` → khớp hoàn toàn.

### Tóm tắt 2 thay đổi đã sửa trong code:

| Thay đổi | Trước | Sau |
|----------|-------|-----|
| Loại cảm biến nhiệt | `DHT22` | `DHT11` ← đã sửa |
| Module công suất | Bạn đổi dây D27 → D33 | Code giữ `PIN_ACS712 = 33` ✅ |

---

## PHẦN 1: CÀI 3 THƯ VIỆN

### Mở Library Manager:

```
Bước 1: Trong Arduino IDE, click menu  Sketch  (trên thanh menu)
Bước 2: Click  Include Library
Bước 3: Click  Manage Libraries...

Hoặc nhanh hơn: Bấm tổ hợp phím  Ctrl + Shift + I
```

> ⏳ Cửa sổ Library Manager hiện ra (bên trái hoặc popup)

---

### Thư viện 1: PubSubClient

```
Bước 1: Trong ô tìm kiếm "Filter your search...", gõ:
        PubSubClient

Bước 2: Tìm đúng kết quả:
        ┌──────────────────────────────────────┐
        │  PubSubClient                         │
        │  by Nick O'Leary                      │  ← ĐÚNG TÁC GIẢ NÀY
        │  Version 2.8                          │
        │  A client library for MQTT messaging  │
        └──────────────────────────────────────┘

⚠️ KHÔNG chọn nhầm thư viện khác!

Bước 3: Click nút  INSTALL  (màu xanh)
Bước 4: Chờ đến khi nút đổi thành  INSTALLED  (hoặc chữ xám)
```

✅ Xong thư viện 1!

---

### Thư viện 2: DHT sensor library

```
Bước 1: Xóa ô tìm kiếm, gõ lại:
        DHT sensor library

Bước 2: Tìm đúng kết quả:
        ┌──────────────────────────────────────┐
        │  DHT sensor library                   │
        │  by Adafruit                          │  ← ĐÚNG TÁC GIẢ NÀY
        │  Version 1.4.x                       │
        └──────────────────────────────────────┘

⚠️ KHÔNG chọn "DHT11", "SimpleDHT", hay "DHTlib"!
   Phải đúng tên: "DHT sensor library" by Adafruit

Bước 3: Click  INSTALL

Bước 4: ❗ NẾU hiện popup hỏi:
        "Would you like to install all missing dependencies?"
        → Click  INSTALL ALL
        (Nó sẽ cài thêm "Adafruit Unified Sensor" tự động)

Bước 5: Chờ đến khi hiện  INSTALLED
```

✅ Xong thư viện 2!

---

### Thư viện 3: ArduinoJson

```
Bước 1: Xóa ô tìm kiếm, gõ lại:
        ArduinoJson

Bước 2: Tìm đúng kết quả:
        ┌──────────────────────────────────────┐
        │  ArduinoJson                          │
        │  by Benoit Blanchon                   │  ← ĐÚNG TÁC GIẢ
        │  Version 6.x.x hoặc 7.x.x           │
        └──────────────────────────────────────┘

⚠️ QUAN TRỌNG VỀ PHIÊN BẢN:
   - Nếu hiện bản 7.x → vẫn dùng được, code tương thích
   - Nếu muốn chắc chắn → click mũi tên version → chọn bản 6.21.x

Bước 3: Click  INSTALL
Bước 4: Chờ đến khi hiện  INSTALLED
```

✅ Xong thư viện 3! Đóng Library Manager.

---

## PHẦN 2: KIỂM TRA WiFi ĐÃ SỬA CHƯA

> Bạn đã sửa WiFi rồi (tôi thấy trong code). Kiểm tra lại cho chắc:

```
Bước 1: Bấm  Ctrl + G  → gõ  24  → Enter
        (Nhảy đến dòng 24)

Bước 2: Xác nhận 2 dòng 24-25 đúng WiFi của bạn:
```

```cpp
// Dòng 24:
const char* WIFI_SSID     = "VIETTEL_";      // ← Tên WiFi bạn
// Dòng 25:
const char* WIFI_PASSWORD = "123456a@";       // ← Mật khẩu WiFi bạn
```

> ✅ Tôi thấy bạn đã sửa thành "VIETTEL_" và "123456a@"
> Nếu đúng WiFi nhà bạn → KHÔNG CẦN SỬA GÌ THÊM.

> ⚠️ Lưu ý:
> - WiFi phải là băng tần **2.4GHz** (ESP32 không hỗ trợ 5GHz)
> - Nếu router có cả 2.4G và 5G, chọn tên WiFi có đuôi "2.4G" hoặc không có đuôi "5G"

---

## PHẦN 3: NẠP CODE (UPLOAD)

### Checklist trước khi nạp:

```
☐ Board:  Tools → Board → esp32 → "ESP32 Dev Module"
☐ Port:   Tools → Port → COMx (cổng có tên ESP32/CH340/CP2102)
☐ Cáp USB đang cắm, đèn LED trên ESP32 đang sáng
☐ Đã đổi dây module công suất từ D27 sang D33
```

### Bấm Upload:

```
Bước 1: Click nút  →  (mũi tên phải) trên thanh công cụ phía trên
        Hoặc bấm  Ctrl + U
        Hoặc menu  Sketch → Upload
```

> ⏳ Arduino IDE sẽ làm 2 giai đoạn:

```
Giai đoạn 1 — COMPILING (biên dịch):
  Thanh tiến trình chạy ở dưới cùng
  Chờ 30-90 giây (lần đầu lâu hơn)
  Output hiện: "Compiling sketch..."

Giai đoạn 2 — UPLOADING (nạp vào mạch):
  Hiện dòng: "Connecting........"
  Rồi chạy phần trăm: 10%... 50%... 100%
  Cuối cùng hiện: "Hard resetting via RTS pin..."
```

### ⚠️ NẾU BỊ KẸT Ở "Connecting........" (chấm chấm lặp lại mãi):

```
╔══════════════════════════════════════════════════════╗
║  GIẢI PHÁP: GIỮ NÚT BOOT TRÊN MẠCH ESP32          ║
║                                                      ║
║  1. Nhìn trên mạch ESP32, tìm nút nhỏ ghi "BOOT"  ║
║     (thường nằm bên trái, gần cổng USB)             ║
║                                                      ║
║  2. GIỮ nút BOOT (nhấn và không thả)               ║
║                                                      ║
║  3. Chờ 2-3 giây → THẢ nút BOOT                    ║
║                                                      ║
║  4. Quá trình upload sẽ bắt đầu chạy %             ║
╚══════════════════════════════════════════════════════╝
```

### ✅ Upload thành công sẽ thấy (chữ TRẮNG, không có chữ đỏ):

```
Leaving...
Hard resetting via RTS pin...
```

### ❌ Nếu lỗi chữ ĐỎ — Bảng xử lý:

| Lỗi | Cách sửa |
|-----|----------|
| `Failed to connect to ESP32` | Giữ nút **BOOT** trên mạch rồi bấm Upload lại |
| `'DHT' was not declared` | Chưa cài thư viện DHT → quay lại cài ở Phần 1 |
| `'PubSubClient' not found` | Chưa cài PubSubClient → quay lại cài ở Phần 1 |
| `Board at COMx is not available` | Rút cáp → cắm lại → Tools → Port → chọn lại COM |
| `espressif:esp32 not installed` | Chưa cài gói ESP32 trong Boards Manager |
| `exit status 1` + lỗi compile | Chụp ảnh dòng lỗi đỏ, gửi cho tôi xem |

---

## PHẦN 4: MỞ SERIAL MONITOR KIỂM TRA

```
Bước 1: Click biểu tượng  🔍 (kính lúp)  ở góc TRÊN BÊN PHẢI
        Hoặc menu  Tools → Serial Monitor
        Hoặc bấm  Ctrl + Shift + M

Bước 2: Ở góc dưới bên phải cửa sổ Serial Monitor
        Tìm dropdown tốc độ (thường ghi "9600 baud")
        → Đổi thành:  115200 baud

Bước 3: Nếu không thấy gì → nhấn nút  EN  (Reset) trên mạch ESP32
```

### ✅ Nếu mọi thứ OK, bạn sẽ thấy:

```
========================================
  SMART CITY — ESP32 Firmware v1.0
========================================
[WiFi] Đang kết nối: VIETTEL_...
......
[WiFi] Đã kết nối — IP: 192.168.1.xxx    ← ✅ WiFi OK
[DHT22] Đã khởi động
[MQTT] Đang kết nối HiveMQ... Thành công! ← ✅ MQTT OK
[MQTT] Đã subscribe: smartcity/control
[Setup] Hoàn tất! Bắt đầu thu thập dữ liệu...

[MQTT] Đã gửi → {"nhiet_do":28.5,"do_am":65,...}  ← ✅ Đang gửi data!
[MQTT] Đã gửi → {"nhiet_do":28.6,"do_am":64,...}
```

> 🎉 **Khi thấy "Thành công!" và "Đã gửi →"** = ESP32 hoạt động tốt!

### ❌ Nếu Serial Monitor hiện lỗi:

| Hiện tượng | Cách sửa |
|-----------|----------|
| Ký tự loạn `⸮⸮⸮` | Đổi baud rate thành **115200** |
| `[WiFi] Thất bại!` lặp lại | Sai tên/mật khẩu WiFi → sửa dòng 24-25, Upload lại |
| WiFi OK nhưng `[MQTT] rc=-2` | Mạng chặn MQTT → thử dùng hotspot điện thoại |
| `[DHT22] Lỗi đọc cảm biến!` | Kiểm tra dây DHT11 trên D4, đảm bảo cắm chặt |
| Không hiện gì | Nhấn nút **EN** (Reset) trên mạch |

---

## PHẦN 5: SAU KHI ESP32 CHẠY OK

> Khi Serial Monitor báo "MQTT thành công", chạy backend trên máy tính:

```bash
cd D:\DAIHOCDAINAM\THONGMINH\smartcity_dashboard\smartcity
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> Mở trình duyệt: **http://localhost:8000**
> Dashboard sẽ hiển thị dữ liệu THẬT từ cảm biến! 🎉
