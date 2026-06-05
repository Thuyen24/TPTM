# ✅ BƯỚC 1 — Trải Thảm Bối Cảnh

## Xác nhận kiến trúc hệ thống

> **Tôi đã hiểu bối cảnh, sẵn sàng nhận lệnh.**

Kiến trúc **4 khối** được khoá chặt như sau:

```
┌─────────────────────────────────────────────────────────────────┐
│                 LUỒNG HỆ THỐNG THỰC DỤNG                       │
│                                                                 │
│  [Cảm biến]                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────┐   JSON/MQTT   ┌──────────────┐   SQLite          │
│  │  ESP32   │──────────────▶│   FastAPI    │──────────────┐    │
│  │  (C++)   │◀──────────────│  (Python)    │              │    │
│  └──────────┘  smartcity/   └──────┬───────┘              │    │
│  ┌──────────┐  control             │ REST API             ▼    │
│  │  Relay   │                      ▼                  ┌──────┐ │
│  │ LOW trig │              ┌──────────────┐           │  DB  │ │
│  └──────────┘              │  index.html  │           │.sqlite│ │
│                            │  (HTML/JS)   │           └──────┘ │
│                            └──────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

| Khối | Công nghệ | Nhiệm vụ |
|------|-----------|----------|
| **Tầng 1 – Thu thập** | ESP32 (C++ / Arduino IDE) | Đọc cảm biến, đóng gói JSON, Publish MQTT |
| **Tầng 2 – Truyền tin** | HiveMQ Public Broker | MQTT Broker trung gian, miễn phí |
| **Tầng 3 – Xử lý & Lưu** | Python / FastAPI + SQLite | Subscribe MQTT, lưu DB, cung cấp REST API |
| **Tầng 4 – Hiển thị** | HTML + Chart.js + Tailwind | Dashboard real-time, cảnh báo, điều khiển |

> ⚠️ **Lưu ý đặc biệt đã ghi nhớ:** Module Relay 1 kênh dùng kích mức **THẤP (LOW level trigger)** → `LOW` = BẬT, `HIGH` = TẮT.

---

# ✅ BƯỚC 2 — Sơ Đồ Đấu Nối Phần Cứng

## Danh sách linh kiện

| STT | Linh kiện | Số lượng | Ghi chú |
|-----|-----------|----------|---------|
| 1 | ESP32 (30 chân) | 1 | NodeMCU ESP32 hoặc tương đương |
| 2 | Adapter 5V 2A + Module MB102 | 1 bộ | Jumper MB102 set **5V** |
| 3 | Cảm biến DHT22 | 1 | Nhiệt độ & Độ ẩm |
| 4 | Cảm biến MQ-135 | 1 | Chất lượng không khí / khí gas |
| 5 | Cảm biến IR hồng ngoại | 2 | Đếm xe (vào & ra) |
| 6 | Cảm biến mực nước | 1 | Analog output |
| 7 | Quang trở LDR | 1 | Cảm biến ánh sáng |
| 8 | Cảm biến dòng điện ACS712 | 1 | Module 5A hoặc 20A |
| 9 | Module Relay 1 kênh | 1 | **LOW level trigger** |
| 10 | LED 5mm (xanh/đỏ) | 2–3 | Trạng thái hệ thống |
| 11 | Điện trở 220Ω | 3 | Nối tiếp LED |
| 12 | Điện trở 10kΩ | 2 | Pull-up DHT22 & LDR |
| 13 | Breadboard 830 lỗ | 1 | |
| 14 | Dây cắm (jumper wire) | ≥30 | |

---

## ⚡ Phân tích nguồn điện — Quan trọng nhất!

```
MB102 Power Supply Module
  ├── Jumper OUTPUT: [5V]  ← Phải set ở đây
  ├── Dải ĐỎ  (+) Breadboard → 5V  (cấp cho Relay, MQ-135, ACS712, IR)
  └── Dải XANH (-) Breadboard → GND (chung toàn mạch)

ESP32 (tự có bộ ổn áp 3.3V)
  ├── 3V3 pin → cấp 3.3V cho DHT22, Water Level, LDR
  └── GND pin → nối vào dải XANH Breadboard
```

> ⚠️ **QUY TẮC AN TOÀN**: ESP32 chỉ chịu tối đa **200mA** trên tổng tất cả GPIO.  
> Relay, MQ-135, ACS712 **PHẢI** lấy VCC từ **dải ĐỎ (5V MB102)**, **KHÔNG** cắm vào pin 3V3 của ESP32.

---

## 📌 Bảng Sơ Đồ Chân (Pinout) Đầy Đủ

### 🔴 Khối nguồn (MB102 → Breadboard)
| Từ | Đến | Màu dây |
|----|-----|---------|
| MB102 OUT (+) | Dải ĐỎ Breadboard | ĐỎ |
| MB102 OUT (–) | Dải XANH Breadboard | ĐEN |
| ESP32 GND | Dải XANH Breadboard | ĐEN |

---

### 🌡️ DHT22 — Nhiệt độ & Độ ẩm
> Nguồn từ ESP32 3V3 (tiêu thụ thấp, an toàn)

| Chân DHT22 | Nối đến | Ghi chú |
|-----------|---------|---------|
| VCC (chân 1) | ESP32 **3V3** | Hoặc dải ĐỎ nếu DHT22 hỗ trợ 5V |
| DATA (chân 2) | ESP32 **GPIO 4** | Thêm điện trở **10kΩ** pull-up từ DATA lên VCC |
| NC (chân 3) | Để hở | |
| GND (chân 4) | Dải **XANH** | |

```
DHT22 Pin2 (DATA) ──┬── GPIO4 (ESP32)
                    │
                   10kΩ
                    │
                  3V3 (ESP32)
```

---

### 💨 MQ-135 — Chất lượng không khí
> Nguồn bắt buộc từ 5V MB102 (sợi nung bên trong cần 5V, tiêu thụ ~150mA)

| Chân MQ-135 | Nối đến | Ghi chú |
|------------|---------|---------|
| VCC | Dải **ĐỎ (5V)** | **BẮT BUỘC** từ MB102 |
| GND | Dải **XANH** | |
| AOUT | ESP32 **GPIO 34** | Analog In — GPIO34 chỉ đọc, không dùng làm output |
| DOUT | Không dùng | (Có thể nối GPIO35 nếu muốn ngưỡng số) |

> ⚠️ ESP32 ADC chỉ đọc được **0–3.3V**. AOUT của MQ-135 có thể lên ~4V khi khí cao.  
> **Giải pháp**: Dùng cầu phân áp: AOUT → R1(10kΩ) → GPIO34 → R2(20kΩ) → GND  
> Điện áp vào GPIO34 = AOUT × 20/(10+20) ≈ AOUT × 0.67 (an toàn cho ESP32)

```
AOUT (MQ135) ──── 10kΩ ──── GPIO34 (ESP32)
                             │
                            20kΩ
                             │
                            GND
```

---

### 🚗 IR Hồng ngoại 1 & 2 — Đếm xe
> Nguồn từ 5V (IR module thường hỗ trợ 3.3V–5V, lấy từ MB102 cho ổn định)

| Chân IR #1 | Nối đến | Chân IR #2 | Nối đến |
|-----------|---------|-----------|---------|
| VCC | Dải **ĐỎ (5V)** | VCC | Dải **ĐỎ (5V)** |
| GND | Dải **XANH** | GND | Dải **XANH** |
| OUT | ESP32 **GPIO 18** | OUT | ESP32 **GPIO 19** |

> ✅ OUT của IR module đã có tín hiệu số (0/1) nên đọc trực tiếp không cần ADC.  
> Cài `INPUT_PULLUP` cho GPIO 18, 19 để tránh trạng thái lơ lửng.

---

### 💧 Cảm biến mực nước — Water Level
> Nguồn 3.3V (tiêu thụ rất thấp)

| Chân | Nối đến | Ghi chú |
|------|---------|---------|
| VCC (+) | ESP32 **3V3** | |
| GND (–) | Dải **XANH** | |
| S (Signal) | ESP32 **GPIO 35** | ADC — GPIO35 chỉ đọc |

> Giá trị ADC (0–4095) tương ứng tỉ lệ mực nước 0%–100%.  
> Threshold cảnh báo: nếu giá trị ADC > 2867 (≈ 70%) → `ngap_lut: true`

---

### ☀️ LDR — Quang trở (ánh sáng)

| Kết nối | Chi tiết |
|---------|---------|
| LDR chân 1 | ESP32 **3V3** |
| LDR chân 2 | ESP32 **GPIO 32** và một đầu điện trở **10kΩ** |
| Đầu kia điện trở 10kΩ | Dải **XANH (GND)** |

```
3V3 ─── [LDR] ─── GPIO32 (ESP32)
                      │
                    10kΩ
                      │
                    GND
```
> Ánh sáng mạnh → điện trở LDR nhỏ → điện áp GPIO32 cao → ADC lớn  
> Đêm tối → LDR trở kháng lớn → ADC nhỏ → có thể trigger bật đèn đường

---

### ⚡ ACS712 — Cảm biến dòng điện
> Nguồn bắt buộc 5V từ MB102 (IC nội bộ cần 5V chính xác)

| Chân ACS712 | Nối đến | Ghi chú |
|------------|---------|---------|
| VCC | Dải **ĐỎ (5V)** | **BẮT BUỘC** từ MB102 |
| GND | Dải **XANH** | |
| VIOUT | Cầu phân áp → **GPIO 33** | Xem sơ đồ dưới |

> ⚠️ VIOUT trung tâm = 2.5V (tại 0A, nguồn 5V). Khi có dòng điện có thể lên/xuống ±~0.5V/A.  
> Cần cầu phân áp để đảm bảo an toàn cho ESP32 ADC (max 3.3V):

```
VIOUT (ACS712) ── 10kΩ ── GPIO33 (ESP32)
                               │
                             20kΩ
                               │
                             GND
```
> Điện áp vào GPIO33 = VIOUT × 0.667 → max ≈ 3.33V (biên độ an toàn)

---

### 🔌 Module Relay 1 kênh — Kích mức THẤP

> **BẮT BUỘC** nguồn 5V từ MB102 (cuộn dây relay cần ~70–90mA)

| Chân Relay | Nối đến | Ghi chú |
|-----------|---------|---------|
| VCC | Dải **ĐỎ (5V)** | **BẮT BUỘC** từ MB102 |
| GND | Dải **XANH** | |
| IN (Signal) | ESP32 **GPIO 26** | LOW = BẬT relay, HIGH = TẮT relay |
| COM | Nguồn phụ tải (dây pha) | Đầu vào của thiết bị cần điều khiển |
| NO | Tải (đầu ra) | Thường mở — khi relay BẬT thì COM nối NO |
| NC | Không dùng | Thường đóng |

> ✅ **Khởi tạo an toàn**: Luôn `digitalWrite(26, HIGH)` trong `setup()` để đảm bảo relay TẮT khi mới khởi động.

---

### 💡 LED trạng thái

| LED | Chân ESP32 | Điện trở | Ý nghĩa |
|-----|-----------|---------|---------|
| LED Xanh | GPIO 27 | 220Ω nối tiếp | WiFi/System OK |
| LED Đỏ | GPIO 25 | 220Ω nối tiếp | Cảnh báo / Lỗi |

```
GPIO27 ── [220Ω] ── [LED Xanh (+)] ── GND
GPIO25 ── [220Ω] ── [LED Đỏ (+)]   ── GND
```

---

## 📋 Tổng hợp bảng GPIO ESP32

| GPIO | Chức năng | Loại | Linh kiện |
|------|-----------|------|-----------|
| **GPIO 4** | DHT22 DATA | Digital I/O | DHT22 |
| **GPIO 18** | IR Sensor 1 | Digital IN | Hồng ngoại #1 (xe vào) |
| **GPIO 19** | IR Sensor 2 | Digital IN | Hồng ngoại #2 (xe ra) |
| **GPIO 25** | LED Đỏ cảnh báo | Digital OUT | LED 5mm + 220Ω |
| **GPIO 26** | Điều khiển Relay | Digital OUT | Relay IN (LOW trigger) |
| **GPIO 27** | LED Xanh | Digital OUT | LED 5mm + 220Ω |
| **GPIO 32** | LDR ánh sáng | ADC IN | LDR + 10kΩ |
| **GPIO 33** | ACS712 dòng điện | ADC IN | ACS712 VIOUT (qua cầu phân áp) |
| **GPIO 34** | MQ-135 khí gas | ADC IN | MQ-135 AOUT (qua cầu phân áp) |
| **GPIO 35** | Mực nước | ADC IN | Water Level sensor |

> 📌 GPIO 32–39 là **Input Only** trên ESP32, không xuất được tín hiệu — đúng với thiết kế trên.

---

## 🗺️ Sơ đồ tổng thể Breadboard (dạng text)

```
       [MB102 Power Module]
          5V OUT ──── Dải ĐỎ (+)
          GND  ──── Dải XANH (-)
                         │
          ┌──────────────┴────────────────────────────────┐
          │              Breadboard                        │
          │                                                │
          │  [ESP32 - 30 chân]                            │
          │   3V3 ──► DHT22.VCC                           │
          │   3V3 ──► WaterLevel.VCC                      │
          │   3V3 ──► LDR.leg1                            │
          │   GND ──► Dải XANH                            │
          │                                                │
          │   GPIO4  ◄── DHT22.DATA (+ 10kΩ pullup)      │
          │   GPIO18 ◄── IR#1.OUT                         │
          │   GPIO19 ◄── IR#2.OUT                         │
          │   GPIO32 ◄── LDR divider                      │
          │   GPIO33 ◄── ACS712.VIOUT (cầu phân áp)      │
          │   GPIO34 ◄── MQ135.AOUT (cầu phân áp)        │
          │   GPIO35 ◄── WaterLevel.S                     │
          │   GPIO25 ──► LED Đỏ ── 220Ω ── GND           │
          │   GPIO26 ──► Relay.IN                         │
          │   GPIO27 ──► LED Xanh ── 220Ω ── GND         │
          │                                                │
          │  Từ Dải ĐỎ (5V):                             │
          │   ──► MQ135.VCC                               │
          │   ──► ACS712.VCC                              │
          │   ──► IR#1.VCC                                │
          │   ──► IR#2.VCC                                │
          │   ──► Relay.VCC                               │
          └────────────────────────────────────────────────┘
```
