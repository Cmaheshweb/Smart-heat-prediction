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