# 🏙️ MÔ TẢ LUỒNG HOẠT ĐỘNG TOÀN DIỆN (v4.0) — SMART CITY DASHBOARD

> **Đề tài**: Bảng Điều Khiển Trung Tâm Cho Thành Phố Thông Minh
> **Đơn vị**: Khoa Công nghệ Thông tin — Trường Đại học Đại Nam
> **Cấu trúc tài liệu**: Phân tích chi tiết quy trình xử lý dữ liệu 4 tầng độc lập, giao thức truyền tin, định dạng gói tin và các cơ chế tối ưu hóa thời gian thực.

---

## 1. SƠ ĐỒ KIẾN TRÚC & LUỒNG DỮ LIỆU TỔNG QUAN

Hệ thống được thiết kế khép kín theo mô hình kiến trúc IoT 4 lớp (Tầng thu thập $\rightarrow$ Tầng truyền dẫn $\rightarrow$ Tầng xử lý/lưu trữ $\rightarrow$ Tầng giám sát/điều khiển). 

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                      KIẾN TRÚC HỆ THỐNG SMART CITY v4.0                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  [ TẦNG 1: THU THẬP DỮ LIỆU & PHẢN HỒI VẬT LÝ ]                            ║
║  • Cảm biến Analog (ADC1): MQ-135 (D34), Water Level (D35), LDR (D32),    ║
║    ACS712 (D33).                                                          ║
║  • Cảm biến Digital (Interrupts): IR1 (D18), IR2 (D19) - Đếm xe <1ms      ║
║  • Cơ cấu chấp hành tại chỗ: LED Đỏ (D2), LED Xanh Dương (D4), LED        ║
║    Xanh Lá (D13), Relay tự động xả bơm (D26).                             ║
║                                                                           ║
║                                    │                                      ║
║                       (MQTT over WiFi Client)                             ║
║                                    ▼                                      ║
║                                                                           ║
║  [ TẦNG 2: TRUYỀN DẪN DỮ LIỆU - MQTT CLOUD BROKER ]                      ║
║  • Host: broker.hivemq.com (Port: 1883)                                   ║
║  • Topic định kỳ (Sensors): smartcity/sensors                             ║
║  • Topic sự kiện xe (Vehicle): smartcity/vehicle                          ║
║  • Topic lệnh điều khiển (Control): smartcity/control                     ║
║                                                                           ║
║                                    │                                      ║
║                            (TCP Connection)                               ║
║                                    ▼                                      ║
║                                                                           ║
║  [ TẦNG 3: MÁY CHỦ TRUNG TÂM - FASTAPI BACKEND (PYTHON) ]                ║
║  • MQTT Subscriber Thread (Chạy nền bất đồng bộ)                          ║
║  • SQLite Database (smartcity.db - Lưu trữ lịch sử vĩnh viễn)              ║
║  • SSE (Server-Sent Events) Publisher: Đẩy sự kiện xe từ RAM (<200ms)     ║
║  • REST API: GET /api/data/latest, GET /api/data/history, POST /control   ║
║                                                                           ║
║                                    │                                      ║
║                     (HTTP API / SSE EventSource)                          ║
║                                    ▼                                      ║
║                                                                           ║
║  [ TẦNG 4: GIÁM SÁT TRỰC QUAN - WEB DASHBOARD ]                           ║
║  • HTML5 / Tailwind CSS (Cyberpunk Neon Dark Mode)                        ║
║  • Chart.js (Biểu đồ tương tác thời gian thực đồng bộ múi giờ client)     ║
║  • Cảnh báo Banner nhấp nháy khẩn cấp trên giao diện                      ║
║  • Nút nhấn điều khiển Relay ON/OFF gửi API tức thời                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## 2. CHI TIẾT HOẠT ĐỘNG TỪNG TẦNG CÔNG NGHỆ

### 2.1. Tầng 1: Lập trình nhúng và Xử lý tín hiệu trên ESP32
Vi điều khiển ESP32 đóng vai trò là thiết bị biên (Edge Device) chịu trách nhiệm giao tiếp vật lý. Hệ thống tối ưu hóa dữ liệu đầu vào qua các thuật toán nhúng:

#### 2.1.1. Luồng đếm xe tức thời (Hardware Interrupt)
- **Vấn đề**: Việc đọc các cảm biến tương tự và gửi dữ liệu mạng trong hàm `loop()` tốn từ `100ms - 500ms`, nếu xe đi nhanh qua cổng kiểm soát sẽ bị bỏ sót.
- **Giải pháp**: Cấu hình ngắt phần cứng trên 2 chân GPIO:
  - `IR1` (Cổng vào) $\rightarrow$ Pin 18 $\rightarrow$ Ngắt cạnh xuống (`FALLING`).
  - `IR2` (Cổng ra) $\rightarrow$ Pin 19 $\rightarrow$ Ngắt cạnh xuống (`FALLING`).
- **Xử lý ngắt**: Khi xe cắt tia, hàm phục vụ ngắt tương ứng (`onIR1Falling`/`onIR2Falling`) được tải trên RAM nội (`IRAM_ATTR`) chạy ngay lập tức để cập nhật bộ đếm tích lũy và đặt cờ sự kiện `vehicleEventPending = true`. Đồng thời, đèn **LED XANH LÁ** (D13) chớp nháy liên tiếp 3 lần thông qua cấu trúc phi tuần tự (non-blocking millis).

#### 2.1.2. Thuật toán lọc nhiễu dải chết (Deadzone Filter) 40%
- **Vấn đề**: Cảm biến mực nước đặt cố định trong chai nhựa ở góc sa bàn dễ bị rò rỉ điện hoặc bám đọng hơi nước, khiến giá trị RAW luôn lơ lửng quanh mức ~2400 (tương đương 10% - 30% mặc dù chai khô hoàn toàn).
- **Giải pháp**: 
  1. Đọc trung bình 5 mẫu để lọc nhiễu gai điện áp.
  2. Định nghĩa điểm nền khô `WATER_DRY_CAL = 2400`.
  3. Tính toán phần trăm thô: $pct\_raw = \text{constrain}(\text{map}(raw, 2500, 4095, 0, 100), 0, 100)$.
  4. Áp dụng dải chết (Deadzone) 40%: Nếu $pct\_raw \le 40\%$, gán thẳng về $0.0\%$.
  5. Ánh xạ tuyến tính phần dải còn lại từ $40\% - 100\%$ lên thang đo chuẩn $0\% - 100\%$.

#### 2.1.3. Hiệu chuẩn mức nền chất lượng không khí MQ-135
- **Giải pháp**: Do cảm biến khí MQ-135 ở điều kiện phòng sạch bình thường luôn xuất ra giá trị RAW quanh mức 2650 - 2700, mã nguồn thiết lập ngưỡng nền cứng tại `2700`. Mọi giá trị $\le 2700$ sẽ được khoá cứng ở mức an toàn là `400 PPM` (nồng độ CO2 tiêu chuẩn trong tự nhiên). Các giá trị trên 2700 được ánh xạ tuyến tính lên đến 5000 PPM để phản ánh chính xác lượng khí thải phát sinh.

#### 2.1.4. Phản hồi cảnh báo LED vật lý tại chỗ (Local Warning)
ESP32 so sánh trực tiếp các giá trị cảm biến sau khi lọc với ngưỡng sự cố để bật/tắt trực tiếp các đầu ra số:
- **Nguy cơ cháy nổ/Khí thải**: Nồng độ Gas $\ge 2000$ PPM $\rightarrow$ Xuất mức `HIGH` ra **LED ĐỎ** (D2).
- **Ngập lụt đô thị**: Mực nước ngầm trong bể thu gom $\ge 70\%$ $\rightarrow$ Xuất mức `HIGH` ra **LED XANH DƯƠNG** (D4) và xuất mức `LOW` kích hoạt Relay đóng điện bật máy bơm xả nước cứu hộ. Khi nước rút dưới $50\%$, tắt bơm và LED.

---

### 2.2. Tầng 2: Giao thức truyền tin MQTT (Publish/Subscribe)
Dữ liệu gửi từ ESP32 lên Broker và lệnh điều khiển gửi từ Server xuống sa bàn được định tuyến qua các Topic riêng biệt:

| Topic | Hướng truyền | Chu kỳ / Điều kiện | Cấu trúc Payload (JSON) |
|---|---|---|---|
| `smartcity/sensors` | ESP32 $\rightarrow$ Broker | Định kỳ mỗi 3 giây | `{"device_id":"ESP32_Dev","nhiet_do":30.5,"do_am":65.0,"chat_luong_kk":400,"so_xe":2,"total_in":5,"total_out":3,"muc_nuoc":0.0,"anh_sang":85,"cong_suat":12.5,"ngap_lut":0}` |
| `smartcity/vehicle` | ESP32 $\rightarrow$ Broker | Tức thời khi ngắt kích hoạt | `{"so_xe":3,"total_in":6,"total_out":3}` |
| `smartcity/control` | Server $\rightarrow$ ESP32 | Tức thời khi bấm nút trên Web | Chuỗi văn bản thuần: `"ON"` hoặc `"OFF"` |

---

### 2.3. Tầng 3: Máy chủ Backend FastAPI & SQLite
Máy chủ đóng vai trò trung chuyển dữ liệu và quản lý lưu trữ:
- **MQTT Thread**: Khởi chạy một tiến trình con (Daemon Thread) duy trì kết nối tới Broker. Khi có bản ghi từ `smartcity/sensors`, luồng này thực hiện parse JSON và thêm bản ghi vào SQLite.
- **SQLite Database**: Bảng `sensor_data` lưu trữ lịch sử để vẽ biểu đồ và xuất báo cáo. Mã nguồn tự động chạy lệnh di cư dữ liệu (`ALTER TABLE`) để thêm cột `total_in` và `total_out` nếu phát hiện cơ sở dữ liệu cũ.
- **Server-Sent Events (SSE)**: Khi sự kiện đếm xe từ `smartcity/vehicle` gửi đến, backend không cần đợi truy vấn đĩa cứng SQLite mà trực tiếp đẩy thẳng sự kiện này từ bộ nhớ RAM nội dung qua API Stream `/api/vehicle/stream` tới tất cả trình duyệt Web đang kết nối với độ trễ cực thấp (<200ms).

---

### 2.4. Tầng 4: Giao diện Web giám sát (Frontend)
- **Cơ chế tải số liệu**:
  - Web Client thực hiện Polling gọi `GET /api/data/latest` mỗi 2 giây để hiển thị số liệu hiện tại của các cảm biến nhiệt độ, độ ẩm, công suất, ánh sáng, ga, nước.
  - Sử dụng đối tượng `EventSource("/api/vehicle/stream")` để duy trì kết nối lắng nghe SSE đẩy dữ liệu sự kiện xe tức thời từ server, giúp cập nhật biểu đồ lưu lượng xe và các card tổng số lượt vào/ra ngay lập tức.
- **Hiển thị khẩn cấp**:
  - Nếu `ngap_lut == 1` hoặc `chat_luong_kk >= 2000`, hệ thống ẩn banner an toàn màu xanh và hiển thị banner đỏ chớp nháy cảnh báo nguy hiểm.
- **Điều khiển phụ tải**:
  - Người dùng bấm BẬT/TẮT trên Web $\rightarrow$ API `POST /api/control` gửi lệnh xuống Backend $\rightarrow$ Backend Publish sang MQTT $\rightarrow$ ESP32 đóng/ngắt Relay trong vòng dưới 100ms.
- **Đồng bộ hóa múi giờ**:
  - Các mốc thời gian trục X của biểu đồ được định dạng bằng `toLocaleTimeString('vi-VN')` từ trình duyệt của người dùng, triệt tiêu lỗi lệch giờ hệ thống.

---

## 3. CÁC KỊCH BẢN THỬ NGHIỆM ĐIỂN HÌNH

### Kịch bản 1: Giám sát lưu lượng xe thông minh
```
[Xe đi qua IR1] ────────► [ESP32 Ngắt cạnh xuống]
                               │
                               ├─► Nháy LED Xanh lá D13 (3 lần)
                               ├─► total_in ++, so_xe ++
                               └─► MQTT publish "smartcity/vehicle"
                                         │
                                         ▼
                                  [FastAPI Server] ──► (Đẩy qua SSE)
                                                              │
                                                              ▼
                                                        [Web Dashboard]
                                                    Card "Lượt Vào" tăng +1
                                                    Card "Trong Bãi" tăng +1
```

### Kịch bản 2: Cảnh báo và tự động ứng phó lũ lụt
```
[Nước ngập >= 70%] ──────► [ESP32 phát hiện vượt ngưỡng]
                               │
                               ├─► Bật LED Xanh dương D4 vật lý
                               ├─► Kích hoạt Relay D26 (LOW) ──► Máy bơm bật xả lũ
                               └─► MQTT publish "smartcity/sensors" (ngap_lut = 1)
                                         │
                                         ▼
                                  [FastAPI Server] ──► Ghi SQLite DB
                                         │
                                         ▼ (2s polling)
                                  [Web Dashboard]
                              • Banner màu đỏ chớp nháy: "CẢNH BÁO NGẬP LỤT"
                              • Nhãn trạng thái mực nước đổi thành "⚠ NGUY HIỂM"
```
