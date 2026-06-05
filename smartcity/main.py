"""
================================================================
 BƯỚC 4 — BACKEND FASTAPI (Tối ưu v2.0)
 Đề tài: Bảng Điều Khiển Trung Tâm Thành Phố Thông Minh
 File  : main.py
================================================================

 Cải tiến v2.0:
   ✅ Subscribe cả smartcity/vehicle (vehicle-only instant topic)
   ✅ Bộ đệm in-memory: latest_vehicle (cập nhật tức thời từ MQTT)
   ✅ GET /api/vehicle/latest → trả dữ liệu xe từ RAM, không query DB
   ✅ GET /api/vehicle/stream → Server-Sent Events (SSE) push thời gian thực
   ✅ Khi vehicle event đến → push SSE ngay tới tất cả Web client

 Cài đặt và chạy:
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload

 API Endpoints:
   GET  /api/data/latest      → Bản ghi sensor mới nhất (DB)
   GET  /api/data/history     → 20 bản ghi gần nhất (DB)
   GET  /api/vehicle/latest   → Dữ liệu xe mới nhất (RAM, cực nhanh)
   GET  /api/vehicle/stream   → SSE stream — push khi có xe mới
   POST /api/control          → Gửi lệnh ON/OFF/AUTO xuống Relay
   GET  /api/status           → Trạng thái hệ thống
   GET  /                     → Serve file index.html
================================================================
"""

import json
import sqlite3
import asyncio
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# ─── LOGGING ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── CẤU HÌNH MQTT ──────────────────────────────────────────
MQTT_BROKER        = "broker.hivemq.com"
MQTT_PORT          = 1883
MQTT_CLIENT        = "SmartCity_Backend_001"
TOPIC_SENSORS      = "smartcity/sensors"     # Toàn bộ sensor (3s)
TOPIC_VEHICLE      = "smartcity/vehicle"     # ★ Vehicle-only (tức thời)
TOPIC_PUB          = "smartcity/control"

# ─── CẤU HÌNH DATABASE ──────────────────────────────────────
DB_PATH = "smartcity.db"

# ─── BIẾN TOÀN CỤC ──────────────────────────────────────────
mqtt_client_global: mqtt.Client = None

# ★ Bộ đệm in-memory cho vehicle data — cập nhật tức thời từ MQTT
#   Không cần query DB → latency gần = 0 ms từ server
latest_vehicle: dict = {
    "so_xe":    0,
    "total_in": 0,
    "total_out": 0,
    "updated_at": None,
}

# ★ Danh sách SSE client đang kết nối (asyncio Queue mỗi client)
#   Khi có vehicle event → push vào tất cả queue → SSE push ngay tới browser
sse_clients: list[asyncio.Queue] = []
sse_lock = threading.Lock()

# Event loop của FastAPI (dùng để schedule coroutine từ MQTT thread)
_main_loop: asyncio.AbstractEventLoop = None


# ============================================================
#  DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id     TEXT,
            nhiet_do      REAL,
            do_am         REAL,
            chat_luong_kk INTEGER,
            so_xe         INTEGER,
            total_in      INTEGER DEFAULT 0,
            total_out     INTEGER DEFAULT 0,
            muc_nuoc      REAL,
            anh_sang      INTEGER,
            cong_suat     REAL,
            ngap_lut      INTEGER DEFAULT 0,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col in ("total_in", "total_out"):
        try:
            conn.execute(f"ALTER TABLE sensor_data ADD COLUMN {col} INTEGER DEFAULT 0")
        except Exception:
            pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS control_log (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    log.info("[DB] Khởi tạo SQLite thành công: %s", DB_PATH)


def save_sensor_data(payload: dict):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO sensor_data
                (device_id, nhiet_do, do_am, chat_luong_kk,
                 so_xe, total_in, total_out, muc_nuoc, anh_sang, cong_suat, ngap_lut)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.get("device_id", "unknown"),
            payload.get("nhiet_do",  0),
            payload.get("do_am",     0),
            payload.get("chat_luong_kk", 0),
            payload.get("so_xe",     0),
            payload.get("total_in",  0),
            payload.get("total_out", 0),
            payload.get("muc_nuoc",  0),
            payload.get("anh_sang",  0),
            payload.get("cong_suat", 0),
            1 if payload.get("ngap_lut", False) else 0,
        ))
        conn.commit()
    except Exception as e:
        log.error("[DB] Lỗi lưu dữ liệu: %s", e)
    finally:
        conn.close()


def log_control(command: str):
    conn = get_db()
    conn.execute("INSERT INTO control_log (command) VALUES (?)", (command,))
    conn.commit()
    conn.close()


# ============================================================
#  SSE — Broadcast vehicle event tới tất cả browser client
# ============================================================

def _broadcast_vehicle_event(data: dict):
    """
    Gọi từ MQTT thread → schedule broadcast vào asyncio event loop.
    Thread-safe thông qua asyncio.run_coroutine_threadsafe.
    """
    global _main_loop
    if _main_loop is None:
        return

    async def _push():
        msg = json.dumps(data)
        dead = []
        with sse_lock:
            clients = list(sse_clients)
        for q in clients:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        # Xóa client bị ngắt kết nối
        if dead:
            with sse_lock:
                for q in dead:
                    if q in sse_clients:
                        sse_clients.remove(q)

    asyncio.run_coroutine_threadsafe(_push(), _main_loop)


# ============================================================
#  MQTT — Xử lý message
# ============================================================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("[MQTT] Kết nối HiveMQ thành công!")
        client.subscribe(TOPIC_SENSORS)
        client.subscribe(TOPIC_VEHICLE)   # ★ Subscribe thêm topic xe
        log.info("[MQTT] Subscribed: %s | %s", TOPIC_SENSORS, TOPIC_VEHICLE)
    else:
        log.error("[MQTT] Kết nối thất bại, rc=%d", rc)


def on_disconnect(client, userdata, rc):
    log.warning("[MQTT] Mất kết nối (rc=%d). Đang tái kết nối...", rc)


def on_message(client, userdata, msg):
    """Phân loại message theo topic."""
    try:
        raw     = msg.payload.decode("utf-8")
        payload = json.loads(raw)
        topic   = msg.topic

        if topic == TOPIC_VEHICLE:
            # ★ Vehicle-only event từ ESP32 ISR — xử lý ưu tiên cao
            _handle_vehicle_event(payload)

        elif topic == TOPIC_SENSORS:
            # Toàn bộ sensor data — lưu DB như bình thường
            log.info("[MQTT/sensors] %s", raw[:100])
            save_sensor_data(payload)

    except json.JSONDecodeError:
        log.error("[MQTT] Lỗi parse JSON: %s", msg.payload[:80])
    except Exception as e:
        log.error("[MQTT] Lỗi xử lý message: %s", e)


def _handle_vehicle_event(payload: dict):
    """
    Xử lý vehicle event tức thời:
      1. Cập nhật bộ đệm in-memory (latest_vehicle)
      2. Broadcast SSE tới tất cả browser client ngay lập tức
    """
    global latest_vehicle
    now_str = datetime.now().isoformat()

    latest_vehicle = {
        "so_xe":      payload.get("so_xe",    0),
        "total_in":   payload.get("total_in", 0),
        "total_out":  payload.get("total_out", 0),
        "updated_at": now_str,
    }

    log.info("[VEHICLE] ★ Xe cập nhật → so_xe=%d, in=%d, out=%d",
             latest_vehicle["so_xe"], latest_vehicle["total_in"], latest_vehicle["total_out"])

    # Broadcast SSE tới tất cả tab browser đang mở
    _broadcast_vehicle_event(latest_vehicle)


def start_mqtt():
    global mqtt_client_global
    client = mqtt.Client(client_id=MQTT_CLIENT, clean_session=True)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client_global = client
        log.info("[MQTT] Đang kết nối %s:%d ...", MQTT_BROKER, MQTT_PORT)
        client.loop_forever()
    except Exception as e:
        log.error("[MQTT] Không thể kết nối: %s", e)


# ============================================================
#  FASTAPI APP — Lifecycle
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_loop
    _main_loop = asyncio.get_running_loop()  # Lưu loop để MQTT thread dùng

    init_db()

    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    log.info("[App] MQTT thread đã khởi động")

    yield

    log.info("[App] Đang dừng...")
    if mqtt_client_global:
        mqtt_client_global.disconnect()


app = FastAPI(
    title="Smart City Dashboard API",
    description="Backend Bảng Điều Khiển Thành Phố Thông Minh — Tối ưu v2.0",
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================
#  PYDANTIC SCHEMAS
# ============================================================

class ControlCommand(BaseModel):
    command: str  # "ON" | "OFF" | "AUTO"


# ============================================================
#  API: SENSOR DATA
# ============================================================

@app.get("/api/data/latest", summary="Dữ liệu sensor mới nhất (từ DB)")
async def get_latest():
    conn = get_db()
    row  = conn.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()

    if row is None:
        return {
            "id": 0, "device_id": "chưa có dữ liệu",
            "nhiet_do": 0, "do_am": 0, "chat_luong_kk": 0,
            "so_xe": latest_vehicle["so_xe"],
            "total_in":  latest_vehicle["total_in"],
            "total_out": latest_vehicle["total_out"],
            "muc_nuoc": 0, "anh_sang": 0, "cong_suat": 0,
            "ngap_lut": False,
            "created_at": datetime.now().isoformat(),
        }

    # Gộp dữ liệu xe từ RAM (cập nhật hơn DB)
    so_xe    = latest_vehicle["so_xe"]    if latest_vehicle["updated_at"] else row["so_xe"]
    total_in = latest_vehicle["total_in"] if latest_vehicle["updated_at"] else row["total_in"]
    total_out= latest_vehicle["total_out"]if latest_vehicle["updated_at"] else row["total_out"]

    return {
        "id":            row["id"],
        "device_id":     row["device_id"],
        "nhiet_do":      row["nhiet_do"],
        "do_am":         row["do_am"],
        "chat_luong_kk": row["chat_luong_kk"],
        "so_xe":         so_xe,
        "total_in":      total_in,
        "total_out":     total_out,
        "muc_nuoc":      row["muc_nuoc"],
        "anh_sang":      row["anh_sang"],
        "cong_suat":     row["cong_suat"],
        "ngap_lut":      bool(row["ngap_lut"]),
        "created_at":    row["created_at"],
    }


@app.get("/api/data/history", summary="20 bản ghi gần nhất")
async def get_history():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sensor_data ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()

    result = []
    for row in reversed(rows):
        result.append({
            "id":            row["id"],
            "nhiet_do":      row["nhiet_do"],
            "do_am":         row["do_am"],
            "chat_luong_kk": row["chat_luong_kk"],
            "so_xe":         row["so_xe"],
            "total_in":      row["total_in"],
            "total_out":     row["total_out"],
            "muc_nuoc":      row["muc_nuoc"],
            "cong_suat":     row["cong_suat"],
            "ngap_lut":      bool(row["ngap_lut"]),
            "created_at":    row["created_at"],
        })

    return {"count": len(result), "data": result}


# ============================================================
#  ★ API: VEHICLE — Tối ưu tốc độ
# ============================================================

@app.get("/api/vehicle/latest", summary="★ Dữ liệu xe mới nhất (từ RAM — cực nhanh)")
async def get_vehicle_latest():
    """
    Trả dữ liệu xe từ bộ đệm in-memory.
    Không query DB → latency < 1ms.
    Web poll endpoint này mỗi 300ms để cập nhật nhanh.
    """
    return latest_vehicle


@app.get("/api/vehicle/stream", summary="★ SSE Stream — Push khi có xe mới")
async def vehicle_stream():
    """
    Server-Sent Events endpoint.
    Browser kết nối một lần, server push data ngay khi có xe mới.
    Không cần polling — latency = thời gian MQTT (< 500ms từ ESP32 đến browser).
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)

    with sse_lock:
        sse_clients.append(queue)

    log.info("[SSE] Client mới kết nối. Tổng: %d", len(sse_clients))

    async def event_generator() -> AsyncGenerator[str, None]:
        # Gửi dữ liệu hiện tại ngay khi client kết nối
        yield f"data: {json.dumps(latest_vehicle)}\n\n"

        try:
            while True:
                try:
                    # Chờ data mới (timeout 25s → gửi heartbeat để giữ kết nối)
                    data = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat giữ cho kết nối không bị proxy cắt
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            with sse_lock:
                if queue in sse_clients:
                    sse_clients.remove(queue)
            log.info("[SSE] Client ngắt kết nối. Còn: %d", len(sse_clients))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":              "no-cache",
            "X-Accel-Buffering":          "no",       # Tắt Nginx buffering
            "Access-Control-Allow-Origin": "*",
        },
    )


# ============================================================
#  API: RELAY CONTROL
# ============================================================

@app.post("/api/control", summary="Gửi lệnh điều khiển Relay (ON/OFF/AUTO)")
async def control_relay(body: ControlCommand):
    command = body.command.upper().strip()

    if command not in ("ON", "OFF", "AUTO"):
        raise HTTPException(
            status_code=400,
            detail="Lệnh không hợp lệ. Chỉ chấp nhận 'ON', 'OFF' hoặc 'AUTO'."
        )

    if mqtt_client_global is None or not mqtt_client_global.is_connected():
        raise HTTPException(status_code=503, detail="MQTT chưa kết nối.")

    result = mqtt_client_global.publish(TOPIC_PUB, command, qos=1)

    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Lỗi publish MQTT (rc={result.rc})")

    log_control(command)
    log.info("[Control] Đã gửi lệnh Relay: %s", command)

    return {
        "success":   True,
        "command":   command,
        "topic":     TOPIC_PUB,
        "message":   f"Đã gửi lệnh '{command}' xuống ESP32",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
#  API: STATUS
# ============================================================

@app.get("/api/status", summary="Trạng thái hệ thống")
async def get_status():
    conn  = get_db()
    count = conn.execute("SELECT COUNT(*) as cnt FROM sensor_data").fetchone()["cnt"]
    conn.close()

    return {
        "status":         "running",
        "mqtt_connected": mqtt_client_global is not None and mqtt_client_global.is_connected(),
        "total_records":  count,
        "sse_clients":    len(sse_clients),
        "timestamp":      datetime.now().isoformat(),
    }


# ─── Serve Dashboard HTML ────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    html_path = Path("index.html")
    if html_path.exists():
        return FileResponse("index.html")
    return HTMLResponse("""
        <h1>Smart City Dashboard</h1>
        <p>Đặt file <strong>index.html</strong> cùng thư mục với main.py</p>
        <p>Thử API tại: <a href='/docs'>/docs</a></p>
    """)


# ─── Entry point ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
