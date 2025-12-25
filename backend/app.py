from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import psutil
import time
from datetime import datetime
import os

# ==================================================
# APP CONFIG
# ==================================================
app = FastAPI(
    title="Smart Heat Engine API",
    version="4.0",
    description="Live Status + Alerts + ACK/RESOLVE + SQLite (Auto Migration)"
)

DB_FILE = "smart_heat_engine.db"

MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75
ALERT_THRESHOLD = 75

# ==================================================
# DATABASE (AUTO MIGRATION)
# ==================================================
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def migrate_db():
    conn = get_db()
    cur = conn.cursor()

    # alerts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        hit INTEGER,
        state TEXT,
        severity TEXT,
        status TEXT,
        ack_by TEXT,
        ack_time TEXT,
        resolved_time TEXT
    )
    """)

    # live status table (single row)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_status (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        timestamp TEXT,
        cpu REAL,
        ram REAL,
        hit INTEGER,
        state TEXT,
        severity TEXT,
        failsafe INTEGER
    )
    """)

    conn.commit()
    conn.close()

# Run migration at startup
migrate_db()

# ==================================================
# DATA MODELS
# ==================================================
class AckInput(BaseModel):
    ack_by: str

# ==================================================
# CORE LOGIC
# ==================================================
def analyze_hit(hit: int):
    if hit < 60:
        return ("MONITOR", "GREEN", [])
    elif hit < 65:
        return ("WARNING", "YELLOW", ["notify_company"])
    elif hit < 70:
        return ("FAN_ON", "ORANGE", ["fan_on"])
    elif hit < 75:
        return ("FULL_COOLING", "RED", ["fan_on", "fan_speed_high", "cooling_system_on"])
    elif hit < 90:
        return ("DATA_SHIFT", "CRITICAL", [
            "fan_on",
            "fan_speed_high",
            "cooling_system_on",
            "data_shift_gradual"
        ])
    else:
        return ("EMERGENCY_SHUTDOWN", "BLACK", ["shutdown_server"])

# ==================================================
# REAL SENSOR WITH RETRY + FAIL-SAFE
# ==================================================
def read_real_sensor():
    for _ in range(MAX_RETRIES):
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            hit = max(cpu, ram)
            return cpu, ram, hit, 0
        except Exception:
            time.sleep(RETRY_DELAY)

    return None, None, FAILSAFE_DEFAULT_HIT, 1

# ==================================================
# DATABASE HELPERS
# ==================================================
def insert_alert(hit, state, severity):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO alerts (timestamp, hit, state, severity, status)
    VALUES (?, ?, ?, ?, 'OPEN')
    """, (datetime.utcnow().isoformat(), hit, state, severity))
    conn.commit()
    conn.close()

def update_live_status(cpu, ram, hit, state, severity, failsafe):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO live_status
    (id, timestamp, cpu, ram, hit, state, severity, failsafe)
    VALUES (1, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), cpu, ram, hit, state, severity, failsafe))
    conn.commit()
    conn.close()

# ==================================================
# ROUTES
# ==================================================
@app.get("/")
def root():
    return {"message": "Smart Heat Engine API running 🚀"}

@app.get("/api/live-status")
def live_status():
    cpu, ram, hit, failsafe = read_real_sensor()
    state, severity, actions = analyze_hit(hit)

    update_live_status(cpu, ram, hit, state, severity, failsafe)

    if hit >= ALERT_THRESHOLD:
        insert_alert(hit, state, severity)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": cpu,
        "ram": ram,
        "hit": hit,
        "state": state,
        "severity": severity,
        "recommended_actions": actions,
        "alert_active": hit >= ALERT_THRESHOLD,
        "failsafe": bool(failsafe),
        "display_target": "SERVER_TEAM_SCREEN"
    }

@app.get("/api/alerts")
def get_alerts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    alerts = []
    for r in rows:
        alerts.append({
            "id": r[0],
            "timestamp": r[1],
            "hit": r[2],
            "state": r[3],
            "severity": r[4],
            "status": r[5],
            "ack_by": r[6],
            "ack_time": r[7],
            "resolved_time": r[8]
        })

    return {"count": len(alerts), "alerts": alerts}

@app.post("/api/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, data: AckInput):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE alerts
    SET status='ACK', ack_by=?, ack_time=?
    WHERE id=? AND status='OPEN'
    """, (data.ack_by, datetime.utcnow().isoformat(), alert_id))
    conn.commit()
    conn.close()

    return {"message": "Alert acknowledged"}

@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE alerts
    SET status='RESOLVED', resolved_time=?
    WHERE id=? AND status!='RESOLVED'
    """, (datetime.utcnow().isoformat(), alert_id))
    conn.commit()
    conn.close()

    return {"message": "Alert resolved"}

@app.get("/api/live-snapshot")
def live_snapshot():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM live_status WHERE id=1")
    r = cur.fetchone()
    conn.close()

    if not r:
        return {"message": "No data yet"}

    return {
        "timestamp": r[1],
        "cpu": r[2],
        "ram": r[3],
        "hit": r[4],
        "state": r[5],
        "severity": r[6],
        "failsafe": bool(r[7])
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import time
import random
from datetime import datetime

# -----------------------------
# OPTIONAL PSUTIL (SAFE FOR RENDER)
# -----------------------------
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

app = FastAPI(
    title="Smart Heat Engine API",
    version="FINAL-2.0",
    description="Complete Server Heat + Cooling + Data Shifting Engine"
)

# -----------------------------
# CONFIG
# -----------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75
ALERT_THRESHOLD = 60
DATA_SHIFT_START = 75
DATA_SHIFT_FAST = 80
SHUTDOWN_THRESHOLD = 90
MAX_ALERT_HISTORY = 100

# -----------------------------
# STORAGE (IN-MEMORY)
# -----------------------------
alert_history = []

class HitInput(BaseModel):
    hit: int

# -----------------------------
# CORE DECISION LOGIC
# -----------------------------
def analyze_hit(hit: int):
    if hit < 60:
        return {"state": "MONITOR", "severity": "GREEN", "actions": []}

    elif hit < 65:
        return {"state": "WARNING", "severity": "YELLOW", "actions": ["notify_company"]}

    elif hit < 70:
        return {"state": "FAN_ON", "severity": "ORANGE", "actions": ["fan_on"]}

    elif hit < 75:
        return {
            "state": "FULL_COOLING",
            "severity": "RED",
            "actions": ["fan_on", "fan_speed_high", "cooling_system_on"]
        }

    elif hit < 90:
        return {
            "state": "DATA_SHIFT",
            "severity": "CRITICAL",
            "actions": [
                "fan_on",
                "fan_speed_high",
                "cooling_system_on",
                "data_shift"
            ]
        }

    else:
        return {
            "state": "EMERGENCY_SHUTDOWN",
            "severity": "BLACK",
            "actions": ["shutdown_server"]
        }

# -----------------------------
# SENSOR (REAL + FAILSAFE)
# -----------------------------
def read_sensor():
    for _ in range(MAX_RETRIES):
        try:
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                hit = max(cpu, ram)
                return hit, False, cpu, ram
            else:
                hit = random.randint(30, 95)
                return hit, False, None, None
        except Exception:
            time.sleep(RETRY_DELAY)

    return FAILSAFE_DEFAULT_HIT, True, None, None

# -----------------------------
# ALERT LOGGER
# -----------------------------
def log_alert(hit, state, severity, message):
    alert = {
        "id": len(alert_history),
        "time": datetime.utcnow().isoformat(),
        "hit": hit,
        "state": state,
        "severity": severity,
        "message": message,
        "acknowledged": False
    }
    alert_history.insert(0, alert)
    del alert_history[MAX_ALERT_HISTORY:]

# -----------------------------
# API ROUTES
# -----------------------------
@app.get("/")
def root():
    return {"message": "Smart Heat Engine API running 🚀"}

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/status")
def status():
    return {
        "service": "smart-heat-engine",
        "psutil_available": PSUTIL_AVAILABLE,
        "status": "active"
    }

@app.post("/api/analyze")
def analyze(input: HitInput):
    return {"hit": input.hit, **analyze_hit(input.hit)}

# -----------------------------
# LIVE STATUS (MAIN ENGINE)
# -----------------------------
@app.get("/api/live-status")
def live_status():
    hit, failsafe, cpu, ram = read_sensor()
    result = analyze_hit(hit)

    data_shift = False
    data_shift_type = None
    shutdown = False

    if hit >= DATA_SHIFT_START and hit < DATA_SHIFT_FAST:
        data_shift = True
        data_shift_type = "GRADUAL"

    elif hit >= DATA_SHIFT_FAST and hit < SHUTDOWN_THRESHOLD:
        data_shift = True
        data_shift_type = "FAST"

    elif hit >= SHUTDOWN_THRESHOLD:
        shutdown = True

    alert_message = "System Normal"

    if shutdown:
        alert_message = "🚨 EMERGENCY SHUTDOWN INITIATED"
        log_alert(hit, result["state"], result["severity"], alert_message)

    elif data_shift:
        alert_message = f"⚠ DATA SHIFT {data_shift_type} IN PROGRESS"
        log_alert(hit, result["state"], result["severity"], alert_message)

    elif hit >= ALERT_THRESHOLD:
        alert_message = "⚠ HIGH SERVER LOAD WARNING"
        log_alert(hit, result["state"], result["severity"], alert_message)

    return {
        "cpu": cpu,
        "ram": ram,
        "hit": hit,
        "failsafe": failsafe,

        "state": result["state"],
        "severity": result["severity"],
        "actions": result["actions"],

        "data_shift": data_shift,
        "data_shift_type": data_shift_type,
        "shutdown": shutdown,

        "alert_message": alert_message,
        "display_target": "SERVER_TEAM_SCREEN"
    }

# -----------------------------
# ALERT HISTORY API
# -----------------------------
@app.get("/api/alerts")
def get_alerts():
    return {"count": len(alert_history), "alerts": alert_history}

@app.post("/api/alerts/{alert_id}/ack")
def acknowledge(alert_id: int):
    for alert in alert_history:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            return {"status": "acknowledged"}
    return {"error": "Invalid alert id"}

# -----------------------------
# LIVE STATUS SCREEN (HTML)
# -----------------------------
@app.get("/live-screen", response_class=HTMLResponse)
def live_screen():
    return """
<html>
<head>
<meta http-equiv="refresh" content="10">
<title>Live Server Screen</title>
<style>
body{background:#020617;color:#e5e7eb;font-family:sans-serif;padding:20px}
.card{background:#111827;padding:15px;border-radius:8px}
.red{color:#f87171}
.orange{color:#fb923c}
.green{color:#4ade80}
</style>
</head>
<body>
<h1>🖥 LIVE SERVER STATUS</h1>
<div class="card" id="data">Loading...</div>
<script>
fetch('/api/live-status').then(r=>r.json()).then(d=>{
document.getElementById('data').innerHTML = `
CPU: ${d.cpu}<br>
RAM: ${d.ram}<br>
HIT: ${d.hit}<br>
STATE: ${d.state}<br>
SEVERITY: ${d.severity}<br>
DATA SHIFT: ${d.data_shift} ${d.data_shift_type || ''}<br>
SHUTDOWN: ${d.shutdown}<br>
<b>${d.alert_message}</b>
`;
});
</script>
</body>
</html>
"""

# -----------------------------
# ALERT HISTORY SCREEN (HTML)
# -----------------------------
@app.get("/alerts-screen", response_class=HTMLResponse)
def alerts_screen():
    return """
<html>
<head>
<meta http-equiv="refresh" content="10">
<title>Alert History</title>
<style>
body{background:#020617;color:#e5e7eb;font-family:sans-serif;padding:20px}
.alert{background:#111827;padding:12px;margin:10px 0;border-left:6px solid red}
</style>
</head>
<body>
<h1>🚨 ALERT HISTORY</h1>
<div id="alerts">Loading...</div>
<script>
fetch('/api/alerts').then(r=>r.json()).then(d=>{
let html='';
d.alerts.forEach(a=>{
html+=`<div class="alert">
<b>${a.state}</b> | HIT ${a.hit}<br>
${a.message}<br>
ACK: ${a.acknowledged}<br>
${a.time}
</div>`;
});
document.getElementById('alerts').innerHTML = html || 'No alerts';
});
</script>
</body>
</html>
"""
    }