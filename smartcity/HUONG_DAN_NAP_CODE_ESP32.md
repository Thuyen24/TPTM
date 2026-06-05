# 🔧 HƯỚNG DẪN CẦM TAY CHỈ VIỆC — Cài Đặt Arduino IDE & Nạp Code ESP32

> **Dành cho người mới bắt đầu**
> Mỗi bước đều chỉ rõ: click vào đâu, gõ gì, nhìn thấy gì.

---

# ═══════════════════════════════════════════════════
# BƯỚC 1: CÀI ĐẶT ARDUINO IDE HỖ TRỢ ESP32
# ═══════════════════════════════════════════════════

## 1.1. Tải và cài Arduino IDE

> Nếu đã cài rồi thì bỏ qua bước này.

1. Mở trình duyệt, vào: **https://www.arduino.cc/en/software**
2. Nhấn nút **"Windows Win 10 and newer, 64 bits"** để tải
3. Chạy file `.exe` vừa tải → Nhấn **Next** → **I Agree** → **Install** → **Close**
4. Mở Arduino IDE từ Desktop hoặc Start Menu

---

## 1.2. Thêm đường dẫn hỗ trợ ESP32 (Additional Boards Manager URLs)

> **Mục đích**: Arduino IDE mặc định chỉ hỗ trợ mạch Arduino. Bước này thêm "nguồn" để tải gói ESP32.

### Thao tác từng bước:

```
Bước 1: Mở Arduino IDE
Bước 2: Click vào menu  File  (góc trên bên trái)
Bước 3: Click  Preferences...  (dòng gần cuối menu)
```

> ⏳ Một cửa sổ nhỏ hiện ra có tiêu đề "Preferences"

```
Bước 4: Tìm dòng chữ "Additional boards manager URLs:"
         (nằm gần cuối cửa sổ, có ô trống dài bên cạnh)
Bước 5: Click vào ô trống đó
Bước 6: COPY đường link bên dưới và DÁN vào ô:
```

```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

> ⚠️ Nếu ô đã có sẵn link khác (ví dụ link ESP8266), thêm dấu phẩy `,` rồi dán link ESP32 phía sau.

```
Bước 7: Nhấn nút  OK  ở góc dưới cửa sổ Preferences
```

✅ **Xong!** Arduino IDE giờ đã biết nơi tải gói ESP32.

---

## 1.3. Cài đặt gói ESP32 trong Boards Manager

> **Mục đích**: Tải và cài bộ công cụ biên dịch code cho chip ESP32.

### Thao tác từng bước:

```
Bước 1: Click menu  Tools  (trên thanh menu)
Bước 2: Click  Board: "..."  (dòng đầu tiên trong menu Tools)
Bước 3: Click  Boards Manager...  (dòng đầu tiên trong submenu)
```

> ⏳ Cửa sổ Boards Manager mở ra (bên trái hoặc popup)

```
Bước 4: Trong ô tìm kiếm (Search), gõ:   esp32
Bước 5: Chờ 5-10 giây để nó tải danh sách
```

> 👀 Bạn sẽ thấy kết quả hiện ra, tìm đúng dòng:
> **"esp32 by Espressif Systems"**

> ⚠️ **KHÔNG CHỌN NHẦM** các gói khác như "esp32 by Arduino" hay "ESP32-S2".
> Phải đúng tác giả là **Espressif Systems**.

```
Bước 6: Click nút  Install  bên cạnh "esp32 by Espressif Systems"
```

> ⏳ Quá trình tải sẽ mất 3-10 phút (tùy mạng).
> Thanh tiến trình sẽ chạy ở dưới cùng.
> **KHÔNG TẮT** Arduino IDE trong lúc này.

```
Bước 7: Khi thanh tiến trình biến mất và hiện chữ "INSTALLED"
         → Đóng Boards Manager
```

✅ **Xong!** Gói ESP32 đã cài thành công.

---

## 1.4. Chọn đúng Board "ESP32 Dev Module"

> **Mục đích**: Báo cho Arduino IDE biết bạn đang dùng loại mạch nào.

### Thao tác từng bước:

```
Bước 1: Click menu  Tools
Bước 2: Click  Board: "..."
Bước 3: Di chuột vào  esp32  (trong submenu sẽ có mục "esp32")
Bước 4: Một danh sách dài hiện ra → TÌM và click:
         ESP32 Dev Module
```

> 💡 **Mẹo**: Danh sách rất dài, cuộn lên gần đầu. Hoặc nếu có ô tìm kiếm,
> gõ "ESP32 Dev" để lọc nhanh.

```
Bước 5: Kiểm tra lại: Nhìn vào menu Tools → Board
         phải thấy ghi: "ESP32 Dev Module"
```

✅ **Xong!** Board đã được chọn đúng.

---

## 1.5. Cắm cáp USB và chọn cổng COM

### A. Phân biệt cáp sạc và cáp dữ liệu

> ⚠️ **ĐÂY LÀ LỖI PHỔ BIẾN NHẤT** của người mới! Rất nhiều cáp USB
> chỉ có 2 dây (sạc) mà không có dây data.

| Loại cáp | Bên trong | Kết quả |
|----------|----------|---------|
| **Cáp SẠC** (2 dây) | Chỉ có dây đỏ (+5V) và đen (GND) | ❌ Cắm vào máy tính KHÔNG nhận COM |
| **Cáp DATA** (4 dây) | Có thêm dây trắng (D-) và xanh (D+) | ✅ Cắm vào máy tính SẼ NHẬN COM |

### Cách kiểm tra nhanh:

```
1. Cắm cáp USB vào ESP32 và máy tính
2. Nhìn trên mạch ESP32: đèn LED nhỏ có sáng không?
   → Nếu KHÔNG sáng: cáp hỏng hoặc cắm chưa chặt
   → Nếu CÓ sáng: tiếp tục bước dưới

3. Mở  Device Manager  trên Windows:
   → Nhấn phím  Windows + X  → chọn  Device Manager
   → Mở mục  "Ports (COM & LPT)"

4. Nếu THẤY dòng như:
   "USB-SERIAL CH340 (COM3)"  hoặc
   "Silicon Labs CP210x (COM5)"  hoặc
   "USB Serial Device (COM4)"
   → ✅ CÁP DATA — máy đã nhận!

5. Nếu KHÔNG THẤY mục Ports hoặc không có COM nào mới:
   → ❌ Đây là CÁP SẠC — ĐỔI CÁP KHÁC!
```

> 💡 **Mẹo**: Cáp đi kèm theo điện thoại Samsung, Xiaomi thường là cáp data.
> Cáp sạc dự phòng, cáp mua rẻ thường chỉ là cáp sạc.

### B. Cài driver (nếu không nhận COM)

> Nếu cắm cáp data mà vẫn không thấy COM, có thể thiếu driver.

```
ESP32 thường dùng 1 trong 2 chip giao tiếp USB:

● Chip CH340:
  → Tải driver tại: https://www.wch-ic.com/downloads/CH341SER_EXE.html
  → Chạy file → Install → Rút cáp → Cắm lại

● Chip CP2102:
  → Tải driver tại: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
  → Cài đặt → Khởi động lại máy → Cắm lại ESP32
```

### C. Chọn cổng COM trong Arduino IDE

```
Bước 1: Cắm ESP32 vào máy tính bằng cáp DATA
Bước 2: Trong Arduino IDE, click menu  Tools
Bước 3: Click  Port
Bước 4: Chọn cổng COM có ghi tên chip, ví dụ:
         "COM3 (USB-SERIAL CH340)"
         hoặc "COM5"
```

> ⚠️ Nếu có nhiều cổng COM, thử RÚT cáp ESP32 ra → nhìn xem cổng nào BIẾN MẤT
> → cắm lại → cổng đó xuất hiện lại → đó chính là cổng của ESP32.

✅ **Xong Bước 1!** Arduino IDE đã sẵn sàng để nạp code vào ESP32.

---
---

# ═══════════════════════════════════════════════════
# BƯỚC 2: NẠP CODE (FIRMWARE) VÀO ESP32
# ═══════════════════════════════════════════════════

## 2.1. Mở file Firmware

```
Bước 1: Trong Arduino IDE, click menu  File  →  Open...
Bước 2: Duyệt đến thư mục dự án:
         D:\DAIHOCDAINAM\THONGMINH\smartcity_dashboard\smartcity\
Bước 3: Chọn file  BUOC_3_ESP32_firmware.ino
Bước 4: Click  Open
```

> ⏳ Arduino IDE sẽ mở file code. Bạn sẽ thấy code bắt đầu bằng:
> `/* BƯỚC 3 — FIRMWARE ESP32 ...*/`

---

## 2.2. Cài đặt 3 thư viện cần thiết

> **Mục đích**: Code firmware sử dụng 3 thư viện bên ngoài. Phải cài trước khi nạp.

### Cách mở Library Manager:

```
Bước 1: Click menu  Tools
Bước 2: Click  Manage Libraries...
         (hoặc bấm tổ hợp phím  Ctrl + Shift + I)
```

> ⏳ Cửa sổ Library Manager hiện ra

### Thư viện 1: PubSubClient (để giao tiếp MQTT)

```
Bước 1: Trong ô tìm kiếm, gõ:  PubSubClient
Bước 2: Tìm đúng dòng:
         "PubSubClient"
         by Nick O'Leary
         (có mô tả: "A client library for MQTT messaging")

⚠️ KHÔNG CHỌN NHẦM thư viện khác có tên tương tự!
    Phải đúng tác giả: Nick O'Leary

Bước 3: Click nút  Install
Bước 4: Chờ đến khi hiện chữ  INSTALLED
```

### Thư viện 2: DHT sensor library (để đọc cảm biến DHT22)

```
Bước 1: Xóa ô tìm kiếm, gõ lại:  DHT sensor library
Bước 2: Tìm đúng dòng:
         "DHT sensor library"
         by Adafruit

⚠️ KHÔNG CHỌN "DHT11" hay "SimpleDHT"
    Phải đúng: "DHT sensor library" by Adafruit

Bước 3: Click  Install
Bước 4: Nếu hiện popup hỏi "Install dependencies?" → Click  Install All
         (nó sẽ cài thêm thư viện "Adafruit Unified Sensor" tự động)
Bước 5: Chờ đến khi hiện  INSTALLED
```

### Thư viện 3: ArduinoJson (để đóng gói dữ liệu JSON)

```
Bước 1: Xóa ô tìm kiếm, gõ lại:  ArduinoJson
Bước 2: Tìm đúng dòng:
         "ArduinoJson"
         by Benoit Blanchon

⚠️ Phải cài bản 6.x (ví dụ 6.21.x), KHÔNG cài bản 7.x
    Nếu mặc định hiện bản 7 → click mũi tên chọn version → chọn bản 6 mới nhất

Bước 3: Click  Install
Bước 4: Chờ đến khi hiện  INSTALLED
```

```
Bước cuối: Đóng Library Manager
```

✅ **Xong!** Đã cài đủ 3 thư viện: PubSubClient, DHT sensor library, ArduinoJson.

---

## 2.3. Sửa tên WiFi và mật khẩu WiFi

> **Mục đích**: ESP32 cần biết WiFi nhà bạn để kết nối Internet → gửi dữ liệu MQTT.

### Tìm dòng cần sửa:

```
Bước 1: Trong file BUOC_3_ESP32_firmware.ino đang mở
Bước 2: Bấm  Ctrl + G  (Go to Line) → gõ  24  → Enter
         Hoặc cuộn lên gần đầu file, tìm dòng 24-25
```

### Bạn sẽ thấy 2 dòng này (dòng 24-25):

```cpp
const char* WIFI_SSID     = "TEN_WIFI_CUA_BAN";   // ← sửa
const char* WIFI_PASSWORD = "MAT_KHAU_WIFI";        // ← sửa
```

### Cách sửa:

```
Bước 3: Thay "TEN_WIFI_CUA_BAN" bằng tên WiFi thật của bạn
Bước 4: Thay "MAT_KHAU_WIFI" bằng mật khẩu WiFi thật

⚠️ GIỮ NGUYÊN dấu ngoặc kép " " bao quanh!
```

### Ví dụ sau khi sửa:

```cpp
const char* WIFI_SSID     = "WiFi_Nha_Minh";       // Tên WiFi
const char* WIFI_PASSWORD = "12345678";              // Mật khẩu
```

> ⚠️ **Lưu ý quan trọng:**
> - Tên WiFi **phân biệt HOA/thường**: "MyWifi" ≠ "mywifi"
> - Mật khẩu phải **chính xác từng ký tự**
> - WiFi phải là **băng tần 2.4GHz** (ESP32 KHÔNG hỗ trợ 5GHz)
> - Nếu WiFi tên có dấu tiếng Việt → nên đổi tên WiFi thành không dấu

```
Bước 5: Bấm  Ctrl + S  để lưu file
```

✅ **Xong!** File đã sẵn sàng nạp.

---

## 2.4. Nạp code (Upload) vào ESP32

### Kiểm tra trước khi nạp:

```
Checklist (nhìn vào menu Tools):
☐ Board:    "ESP32 Dev Module"         ← đã chọn ở Bước 1.4
☐ Port:     "COM3" (hoặc COMx)        ← đã chọn ở Bước 1.5
☐ ESP32 đang cắm cáp USB vào máy      ← đèn LED trên mạch sáng
```

### Thao tác nạp:

```
Bước 1: Click nút  →  (mũi tên sang phải) trên thanh công cụ
        Hoặc bấm  Ctrl + U
        Hoặc menu  Sketch  →  Upload
```

> ⏳ Arduino IDE sẽ làm 2 việc:
> 1. **Compiling** (biên dịch): Thanh tiến trình chạy, chờ 30-60 giây
> 2. **Uploading** (nạp): Hiện dòng "Connecting........" rồi "%"

### Khi nào cần giữ nút BOOT:

```
Nếu thấy dòng:  "Connecting........___"  lặp lại nhiều lần không chạy tiếp:

→ GIẢI PHÁP: Trên mạch ESP32, tìm nút  BOOT  (nút nhỏ, thường bên trái)
→ GIỮ nút BOOT trong 3 giây rồi THẢ
→ Quá trình upload sẽ bắt đầu chạy %
```

### Upload thành công sẽ thấy:

```
Leaving...
Hard resetting via RTS pin...

Khung output màu TRẮNG, KHÔNG có chữ đỏ lỗi.
```

### ❌ Nếu báo lỗi chữ đỏ — Cách xử lý:

| Lỗi | Nguyên nhân | Cách sửa |
|-----|------------|----------|
| `A fatal error occurred: Failed to connect to ESP32` | ESP32 chưa vào chế độ nạp | **Giữ nút BOOT** trên mạch khi bấm Upload, thả sau khi thấy "Connecting..." |
| `compilation error` / `no such file or directory` | Thiếu thư viện | Quay lại Bước 2.2, cài lại 3 thư viện |
| `'DHT' was not declared` | Chưa cài DHT sensor library | Cài lại thư viện DHT (Bước 2.2) |
| `Board at COM3 is not available` | Sai cổng COM hoặc cáp lỏng | Rút cáp, cắm lại, chọn lại Port trong menu Tools |
| `espressif:esp32 not installed` | Chưa cài gói ESP32 | Quay lại Bước 1.3, cài lại trong Boards Manager |
| `Multiple libraries were found for "DHT.h"` | Cài trùng thư viện | Không sao, chỉ là cảnh báo, code vẫn nạp được |

---

## 2.5. Mở Serial Monitor để kiểm tra

> **Mục đích**: Xem ESP32 có kết nối WiFi và MQTT thành công không.

### Thao tác:

```
Bước 1: Click biểu tượng  🔍 (kính lúp)  ở góc trên bên phải
        Hoặc menu  Tools  →  Serial Monitor
        Hoặc bấm  Ctrl + Shift + M

Bước 2: Ở góc dưới bên phải Serial Monitor, tìm dropdown tốc độ
        Đổi từ "9600 baud" thành:  115200 baud
```

> ⚠️ Nếu chọn sai baud rate sẽ thấy ký tự loạn (?????)
> → Đổi lại thành 115200

### Nếu mọi thứ OK, bạn sẽ thấy:

```
========================================
  SMART CITY — ESP32 Firmware v1.0
========================================
[WiFi] Đang kết nối: WiFi_Nha_Minh...
......
[WiFi] Đã kết nối — IP: 192.168.1.xxx
[DHT22] Đã khởi động
[MQTT] Đang kết nối HiveMQ... Thành công!
[MQTT] Đã subscribe: smartcity/control
[Setup] Hoàn tất! Bắt đầu thu thập dữ liệu...

[MQTT] Đã gửi → {"device_id":"SmartCity_ESP32_001","nhiet_do":28.5,...}
[MQTT] Đã gửi → {"device_id":"SmartCity_ESP32_001","nhiet_do":28.6,...}
```

> 🎉 **Khi thấy dòng "Kết nối MQTT thành công" và "Đã gửi →"**
> → ESP32 đã hoạt động! Đang gửi dữ liệu lên cloud mỗi 2 giây.

### ❌ Nếu Serial Monitor hiện lỗi:

| Hiện tượng | Nguyên nhân | Cách sửa |
|-----------|------------|----------|
| Toàn ký tự loạn `⸮⸮⸮⸮` | Sai baud rate | Đổi thành **115200** |
| `[WiFi] Thất bại! Khởi động lại...` | Sai tên/mật khẩu WiFi | Sửa lại dòng 24-25, Upload lại |
| Kết nối WiFi OK nhưng `[MQTT] Thất bại, rc=-2` | Mạng chặn MQTT hoặc broker bận | Thử lại, đổi mạng WiFi (dùng hotspot điện thoại) |
| `[DHT22] Lỗi đọc cảm biến!` | Dây DHT22 lỏng hoặc chưa cắm | Kiểm tra dây GPIO 4, điện trở 10kΩ |
| Không hiện gì cả | ESP32 chưa reset | Nhấn nút **EN** (Reset) trên mạch |

---

## 2.6. Sau khi ESP32 chạy OK — Chạy Backend & Dashboard

> Khi Serial Monitor đã hiện "MQTT thành công", mở terminal trên máy tính:

```bash
# Bước 1: Mở terminal (PowerShell/CMD), vào thư mục dự án
cd D:\DAIHOCDAINAM\THONGMINH\smartcity_dashboard\smartcity

# Bước 2: Chạy backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Bước 3: Mở trình duyệt
# Truy cập: http://localhost:8000
```

> 🎉 Lúc này Dashboard sẽ hiển thị dữ liệu THẬT từ cảm biến!
> Các số liệu sẽ tự cập nhật mỗi 2 giây.

---

## TÓM TẮT QUY TRÌNH

```
┌─────────────────────────────────────────────────┐
│           QUY TRÌNH NẠP CODE ESP32              │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Cài Arduino IDE                             │
│           ↓                                      │
│  2. Thêm URL ESP32 vào Preferences             │
│           ↓                                      │
│  3. Cài gói "esp32 by Espressif" từ Boards Mgr │
│           ↓                                      │
│  4. Chọn Board: "ESP32 Dev Module"              │
│           ↓                                      │
│  5. Cắm cáp DATA USB → Chọn cổng COM          │
│           ↓                                      │
│  6. Mở file BUOC_3_ESP32_firmware.ino           │
│           ↓                                      │
│  7. Cài 3 thư viện từ Library Manager           │
│     • PubSubClient (Nick O'Leary)               │
│     • DHT sensor library (Adafruit)             │
│     • ArduinoJson v6 (Benoit Blanchon)          │
│           ↓                                      │
│  8. Sửa WiFi dòng 24-25                        │
│           ↓                                      │
│  9. Bấm Upload (→) — Giữ BOOT nếu cần         │
│           ↓                                      │
│  10. Mở Serial Monitor (115200 baud)            │
│           ↓                                      │
│  11. Thấy "MQTT thành công" → XONG! ✅         │
│           ↓                                      │
│  12. Chạy Backend → Mở Dashboard                │
│                                                  │
└─────────────────────────────────────────────────┘
```
