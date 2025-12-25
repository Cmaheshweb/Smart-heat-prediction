# ============================================================
# SMART HEAT ENGINE – FINAL MASTER APP.PY
# ============================================================

"""
FINAL BEHAVIOUR CONTRACT (LOCKED):

0–59%   -> MONITOR
60%     -> COMPANY WARNING
65%     -> FAN ON
70%     -> FULL COOLING
75%     -> GRADUAL DATA SHIFT
80%     -> FAST DATA SHIFT
90%     -> EMERGENCY SHUTDOWN
"""

# ============================================================
# IMPORTS
# ============================================================

import time
import random
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Optional psutil (Render-safe)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ============================================================
# THRESHOLDS (LOCKED)
# ============================================================

THRESH_MONITOR_MAX = 59
THRESH_WARNING = 60
THRESH_FAN_ON = 65
THRESH_FULL_COOLING = 70
THRESH_DATA_SHIFT_GRADUAL = 75
THRESH_DATA_SHIFT_FAST = 80
THRESH_EMERGENCY_SHUTDOWN = 90

# ============================================================
# STATES
# ============================================================

STATE_MONITOR = "MONITOR"
STATE_WARNING = "WARNING"
STATE_FAN_ON = "FAN_ON"
STATE_FULL_COOLING = "FULL_COOLING"
STATE_DATA_SHIFT_GRADUAL = "DATA_SHIFT_GRADUAL"
STATE_DATA_SHIFT_FAST = "DATA_SHIFT_FAST"
STATE_EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"

# ============================================================
# SEVERITY
# ============================================================

SEVERITY_GREEN = "GREEN"
SEVERITY_YELLOW = "YELLOW"
SEVERITY_ORANGE = "ORANGE"
SEVERITY_RED = "RED"
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_BLACK = "BLACK"

# ============================================================
# ACTIONS
# ============================================================

ACTION_NOTIFY_COMPANY = "notify_company"
ACTION_FAN_ON = "fan_on"
ACTION_FAN_SPEED_HIGH = "fan_speed_high"
ACTION_COOLING_SYSTEM_ON = "cooling_system_on"
ACTION_DATA_SHIFT_GRADUAL = "data_shift_gradual"
ACTION_DATA_SHIFT_FAST = "data_shift_fast"
ACTION_EMERGENCY_SHUTDOWN = "shutdown_server"

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Smart Heat Engine",
    version="FINAL",
    description="Production-grade Server Heat Prediction & Control System"
)

# ============================================================
# SYSTEM MEMORY (GLOBAL)
# ============================================================

SYSTEM_MEMORY = {
    "current_state": STATE_MONITOR,
    "data_shift_started": False,
    "shutdown_initiated": False
}

# ============================================================
# PURE DECISION ENGINE (LOCKED)
# ============================================================

def decide_state_from_hit(hit: int):
    if hit <= THRESH_MONITOR_MAX:
        return {"state": STATE_MONITOR, "severity": SEVERITY_GREEN, "actions": []}

    if hit < THRESH_FAN_ON:
        return {"state": STATE_WARNING, "severity": SEVERITY_YELLOW,
                "actions": [ACTION_NOTIFY_COMPANY]}

    if hit < THRESH_FULL_COOLING:
        return {"state": STATE_FAN_ON, "severity": SEVERITY_ORANGE,
                "actions": [ACTION_FAN_ON]}

    if hit < THRESH_DATA_SHIFT_GRADUAL:
        return {"state": STATE_FULL_COOLING, "severity": SEVERITY_RED,
                "actions": [ACTION_FAN_ON, ACTION_FAN_SPEED_HIGH, ACTION_COOLING_SYSTEM_ON]}

    if hit < THRESH_DATA_SHIFT_FAST:
        return {"state": STATE_DATA_SHIFT_GRADUAL, "severity": SEVERITY_CRITICAL,
                "actions": [ACTION_FAN_ON, ACTION_FAN_SPEED_HIGH,
                            ACTION_COOLING_SYSTEM_ON, ACTION_DATA_SHIFT_GRADUAL]}

    if hit < THRESH_EMERGENCY_SHUTDOWN:
        return {"state": STATE_DATA_SHIFT_FAST, "severity": SEVERITY_CRITICAL,
                "actions": [ACTION_FAN_ON, ACTION_FAN_SPEED_HIGH,
                            ACTION_COOLING_SYSTEM_ON, ACTION_DATA_SHIFT_FAST]}

    return {"state": STATE_EMERGENCY_SHUTDOWN, "severity": SEVERITY_BLACK,
            "actions": [ACTION_EMERGENCY_SHUTDOWN]}

# ============================================================
# SENSOR READ (RETRY + FAILSAFE)
# ============================================================

def read_server_hit():
    for _ in range(3):
        try:
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                return int(max(cpu, ram)), cpu, ram, "REAL"
            else:
                return random.randint(30, 95), None, None, "SIMULATED"
        except Exception:
            time.sleep(2)

    return 75, None, None, "FAILSAFE"

# ============================================================
# STATE TRANSITION (LOCKED FORWARD ONLY)
# ============================================================

def transition_state(hit: int):
    if SYSTEM_MEMORY["shutdown_initiated"]:
        return {
            "state": STATE_EMERGENCY_SHUTDOWN,
            "severity": SEVERITY_BLACK,
            "actions": [ACTION_EMERGENCY_SHUTDOWN]
        }

    decision = decide_state_from_hit(hit)
    new_state = decision["state"]

    if new_state in (STATE_DATA_SHIFT_GRADUAL, STATE_DATA_SHIFT_FAST):
        SYSTEM_MEMORY["data_shift_started"] = True

    if SYSTEM_MEMORY["data_shift_started"] and new_state in (
        STATE_MONITOR, STATE_WARNING, STATE_FAN_ON, STATE_FULL_COOLING
    ):
        new_state = STATE_DATA_SHIFT_GRADUAL
        decision = decide_state_from_hit(THRESH_DATA_SHIFT_GRADUAL)

    if new_state == STATE_EMERGENCY_SHUTDOWN:
        SYSTEM_MEMORY["shutdown_initiated"] = True

    SYSTEM_MEMORY["current_state"] = new_state

    return {
        "state": new_state,
        "severity": decision["severity"],
        "actions": decision["actions"]
    }

# ============================================================
# ALERT MEMORY
# ============================================================

ALERT_HISTORY = []

def emit_alert(hit, state, severity, message, source):
    alert = {
        "id": len(ALERT_HISTORY),
        "timestamp": datetime.utcnow().isoformat(),
        "hit": hit,
        "state": state,
        "severity": severity,
        "message": message,
        "source": source,
        "status": "OPEN"
    }
    ALERT_HISTORY.insert(0, alert)
    return alert

# ============================================================
# API ROUTES
# ============================================================

@app.get("/")
def root():
    return {"message": "Smart Heat Engine running"}

@app.get("/api/live-status")
def live_status():
    hit, cpu, ram, source = read_server_hit()
    decision = transition_state(hit)

    state = decision["state"]
    severity = decision["severity"]
    actions = decision["actions"]

    message = "System Normal"
    if state != STATE_MONITOR:
        message = f"{state} ACTIVE"
        emit_alert(hit, state, severity, message, source)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "cpu": cpu,
        "ram": ram,
        "hit": hit,
        "state": state,
        "severity": severity,
        "actions": actions,
        "alert_message": message,
        "display_target": "SERVER_TEAM_SCREEN"
    }

@app.get("/api/alerts")
def alerts():
    return {"count": len(ALERT_HISTORY), "alerts": ALERT_HISTORY}

# ============================================================
# LIVE SCREEN (HTML)
# ============================================================

@app.get("/live-screen", response_class=HTMLResponse)
def live_screen():
    return """
<html>
<head><meta http-equiv="refresh" content="10"></head>
<body style="background:#020617;color:white;font-family:Arial">
<h2>Live Server Status</h2>
<div id="data">Loading...</div>
<script>
fetch('/api/live-status').then(r=>r.json()).then(d=>{
document.getElementById('data').innerHTML =
`HIT: ${d.hit}%<br>STATE: ${d.state}<br>SEVERITY: ${d.severity}<br>${d.alert_message}`;
});
</script>
</body>
</html>
"""

# ============================================================
# ALERT SCREEN
# ============================================================

@app.get("/alerts-screen", response_class=HTMLResponse)
def alerts_screen():
    return """
<html>
<head><meta http-equiv="refresh" content="10"></head>
<body style="background:#020617;color:white;font-family:Arial">
<h2>Alert History</h2>
<div id="alerts">Loading...</div>
<script>
fetch('/api/alerts').then(r=>r.json()).then(d=>{
let html='';
d.alerts.forEach(a=>{
html+=`<div>${a.timestamp} | ${a.state} | HIT ${a.hit}%</div>`;
});
document.getElementById('alerts').innerHTML=html;
});
</script>
</body>
</html>
"""