"""
FINAL BEHAVIOUR CONTRACT (LOCKED):

0–59%   -> MONITOR (observe only)
60%     -> COMPANY WARNING
65%     -> FAN ON
70%     -> FULL COOLING
75%     -> GRADUAL DATA SHIFT
80%     -> FAST DATA SHIFT
90%     -> EMERGENCY SHUTDOWN

This contract MUST NOT change.
All engines must follow this state machine.
"""

# ----------------------------
# THRESHOLDS (LOCKED)
# ----------------------------
THRESH_MONITOR_MAX = 59

THRESH_WARNING = 60
THRESH_FAN_ON = 65
THRESH_FULL_COOLING = 70
THRESH_DATA_SHIFT_GRADUAL = 75
THRESH_DATA_SHIFT_FAST = 80
THRESH_EMERGENCY_SHUTDOWN = 90

# ----------------------------
# SYSTEM STATES (ENUM STYLE)
# ----------------------------
STATE_MONITOR = "MONITOR"
STATE_WARNING = "WARNING"
STATE_FAN_ON = "FAN_ON"
STATE_FULL_COOLING = "FULL_COOLING"
STATE_DATA_SHIFT_GRADUAL = "DATA_SHIFT_GRADUAL"
STATE_DATA_SHIFT_FAST = "DATA_SHIFT_FAST"
STATE_EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"

# ----------------------------
# SEVERITY LEVELS
# ----------------------------
SEVERITY_GREEN = "GREEN"
SEVERITY_YELLOW = "YELLOW"
SEVERITY_ORANGE = "ORANGE"
SEVERITY_RED = "RED"
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_BLACK = "BLACK"

# ----------------------------
# ACTION FLAGS (LOGICAL, NOT PHYSICAL)
# ----------------------------
ACTION_NOTIFY_COMPANY = "notify_company"
ACTION_FAN_ON = "fan_on"
ACTION_FAN_SPEED_HIGH = "fan_speed_high"
ACTION_COOLING_SYSTEM_ON = "cooling_system_on"
ACTION_DATA_SHIFT_GRADUAL = "data_shift_gradual"
ACTION_DATA_SHIFT_FAST = "data_shift_fast"
ACTION_EMERGENCY_SHUTDOWN = "shutdown_server"

# ----------------------------
# STATE DECISION ENGINE (PURE LOGIC)
# ----------------------------
def decide_state_from_hit(hit: int):
    """
    INPUT  : hit percentage (0–100)
    OUTPUT : dict(state, severity, actions)

    This function is PURE.
    No side-effects.
    """

    if hit <= THRESH_MONITOR_MAX:
        return {
            "state": STATE_MONITOR,
            "severity": SEVERITY_GREEN,
            "actions": []
        }

    if hit < THRESH_FAN_ON:
        return {
            "state": STATE_WARNING,
            "severity": SEVERITY_YELLOW,
            "actions": [ACTION_NOTIFY_COMPANY]
        }

    if hit < THRESH_FULL_COOLING:
        return {
            "state": STATE_FAN_ON,
            "severity": SEVERITY_ORANGE,
            "actions": [ACTION_FAN_ON]
        }

    if hit < THRESH_DATA_SHIFT_GRADUAL:
        return {
            "state": STATE_FULL_COOLING,
            "severity": SEVERITY_RED,
            "actions": [
                ACTION_FAN_ON,
                ACTION_FAN_SPEED_HIGH,
                ACTION_COOLING_SYSTEM_ON
            ]
        }

    if hit < THRESH_DATA_SHIFT_FAST:
        return {
            "state": STATE_DATA_SHIFT_GRADUAL,
            "severity": SEVERITY_CRITICAL,
            "actions": [
                ACTION_FAN_ON,
                ACTION_FAN_SPEED_HIGH,
                ACTION_COOLING_SYSTEM_ON,
                ACTION_DATA_SHIFT_GRADUAL
            ]
        }

    if hit < THRESH_EMERGENCY_SHUTDOWN:
        return {
            "state": STATE_DATA_SHIFT_FAST,
            "severity": SEVERITY_CRITICAL,
            "actions": [
                ACTION_FAN_ON,
                ACTION_FAN_SPEED_HIGH,
                ACTION_COOLING_SYSTEM_ON,
                ACTION_DATA_SHIFT_FAST
            ]
        }

    return {
        "state": STATE_EMERGENCY_SHUTDOWN,
        "severity": SEVERITY_BLACK,
        "actions": [ACTION_EMERGENCY_SHUTDOWN]
    }
import time
import random

# Optional psutil (safe for cloud / render)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ----------------------------
# SENSOR CONFIG
# ----------------------------
SENSOR_MAX_RETRIES = 3
SENSOR_RETRY_DELAY = 2  # seconds
FAILSAFE_DEFAULT_HIT = 75

# ----------------------------
# SENSOR READ FUNCTION
# ----------------------------
def read_server_hit():
    """
    Returns:
        hit (int)        -> final server load percentage
        cpu (float|None)
        ram (float|None)
        source (str)     -> REAL / SIMULATED / FAILSAFE
    """

    for _ in range(SENSOR_MAX_RETRIES):
        try:
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                hit = int(max(cpu, ram))
                return hit, cpu, ram, "REAL"

            # Simulation mode (mobile / testing)
            hit = random.randint(30, 95)
            return hit, None, None, "SIMULATED"

        except Exception:
            time.sleep(SENSOR_RETRY_DELAY)

    # ------------------------
    # FAIL-SAFE MODE
    # ------------------------
    return FAILSAFE_DEFAULT_HIT, None, None, "FAILSAFE"
"current_state": STATE_MONITOR,
    "data_shift_started": False,
    "shutdown_initiated": False
}

# ----------------------------
# TRANSITION FUNCTION
# ----------------------------
def transition_state(hit: int):
    """
    INPUT  : hit percentage
    OUTPUT : dict with final state decision

    Rules:
    - State always moves forward, never backward
    - Data shift once started cannot rollback
    - Shutdown once triggered is final
    """
SYSTEM_MEMORY["shutdown_initiated"]:
        return {
            "state": STATE_EMERGENCY_SHUTDOWN,
            "severity": SEVERITY_BLACK,
            "actions": [ACTION_EMERGENCY_SHUTDOWN],
            "locked": True
        }

    # Pure decision (from locked behaviour contract)
    decision = decide_state_from_hit(hit)
    new_state = decision["state"]

    # ------------------------
    # DATA SHIFT LOCK
    # ------------------------
    if new_state in (STATE_DATA_SHIFT_GRADUAL, STATE_DATA_SHIFT_FAST):
        SYSTEM_MEMORY["data_shift_started"] = True
if SYSTEM_MEMORY["data_shift_started"]:
        if new_state in (
            STATE_MONITOR,
            STATE_WARNING,
            STATE_FAN_ON,
            STATE_FULL_COOLING
        ):
            new_state = STATE_DATA_SHIFT_GRADUAL
            decision = decide_state_from_hit(THRESH_DATA_SHIFT_GRADUAL)

    # ------------------------
    # SHUTDOWN LOCK
    # ------------------------
    if new_state == STATE_EMERGENCY_SHUTDOWN:
        SYSTEM_MEMORY["shutdown_initiated"] = True

    # ------------------------
    # UPDATE CURRENT STATE
    # ------------------------
    SYSTEM_MEMORY["current_state"] = new_state

    return {
        "state": new_state,
        "severity": decision["severity"],
        "actions": decision["actions"],
        "locked": SYSTEM_MEMORY["shutdown_initiated"]
    }

# ----------------------------
# SYSTEM RESET (MANUAL ONLY)
# ----------------------------
def manual_system_reset():
    """
    Dangerous operation.
    Should be allowed only by admin in future.
    """
    SYSTEM_MEMORY["current_state"] = STATE_MONITOR
    SYSTEM_MEMORY["data_shift_started"] = False
    SYSTEM_MEMORY["shutdown_initiated"] = False
from datetime import datetime

# ----------------------------
# ALERT CONFIG
# ----------------------------
ALERT_MAX_HISTORY = 500
ALERT_DEDUP_WINDOW_SEC = 60  # duplicate alert avoid window

# ----------------------------
# ALERT STORAGE (IN-MEMORY)
# ----------------------------
ALERT_HISTORY = []  # list of dicts
_LAST_ALERT_FINGERPRINT = None
_LAST_ALERT_TIME = None

# ----------------------------
# ALERT STATES
# ----------------------------
ALERT_STATUS_OPEN = "OPEN"
ALERT_STATUS_ACK = "ACK"
ALERT_STATUS_RESOLVED = "RESOLVED"

# ----------------------------
# ALERT CREATION LOGIC
# ----------------------------
def _make_alert_fingerprint(state: str, severity: str):
    """
    Fingerprint helps avoid duplicate alerts
    """
    return f"{state}:{severity}"

def should_emit_alert(state: str, severity: str):
    """
    Avoids duplicate alerts within a short window
    """
    global _LAST_ALERT_FINGERPRINT, _LAST_ALERT_TIME

    now = time.time()
    fp = _make_alert_fingerprint(state, severity)

    if _LAST_ALERT_FINGERPRINT == fp and _LAST_ALERT_TIME:
        if now - _LAST_ALERT_TIME < ALERT_DEDUP_WINDOW_SEC:
            return False

    _LAST_ALERT_FINGERPRINT = fp
    _LAST_ALERT_TIME = now
    return True

def emit_alert(hit: int, state: str, severity: str, message: str, source: str):
    """
    Creates an alert event
    """
    if not should_emit_alert(state, severity):
        return None

    alert = {
        "id": len(ALERT_HISTORY),
        "timestamp": datetime.utcnow().isoformat(),
        "hit": hit,
        "state": state,
        "severity": severity,
        "message": message,
        "source": source,
        "status": ALERT_STATUS_OPEN,
        "ack_by": None,
        "ack_time": None,
        "resolved_time": None
    }

    ALERT_HISTORY.insert(0, alert)
    del ALERT_HISTORY[ALERT_MAX_HISTORY:]
    return alert

# ----------------------------
# ALERT LIFECYCLE
# ----------------------------
def acknowledge_alert(alert_id: int, user: str = "operator"):
    for alert in ALERT_HISTORY:
        if alert["id"] == alert_id and alert["status"] == ALERT_STATUS_OPEN:
            alert["status"] = ALERT_STATUS_ACK
            alert["ack_by"] = user
            alert["ack_time"] = datetime.utcnow().isoformat()
            return True
    return False

def resolve_alert(alert_id: int):
    for alert in ALERT_HISTORY:
        if alert["id"] == alert_id and alert["status"] != ALERT_STATUS_RESOLVED:
            alert["status"] = ALERT_STATUS_RESOLVED
            alert["resolved_time"] = datetime.utcnow().isoformat()
            return True
    return False
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
try:
    app
except NameError:
    app = FastAPI(
        title="Smart Heat Engine API",
        version="MASTER",
        description="Complete Server Heat Prediction & Control Engine"
    )

# ----------------------------
# BASIC ROUTES
# ----------------------------
@app.get("/")
def root():
    return {"message": "Smart Heat Engine API running"}

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/status")
def system_status():
    return {
        "service": "smart-heat-engine",
        "current_state": SYSTEM_MEMORY["current_state"],
        "data_shift_started": SYSTEM_MEMORY["data_shift_started"],
        "shutdown_initiated": SYSTEM_MEMORY["shutdown_initiated"]
    }

# ----------------------------
# LIVE STATUS ROUTE (CORE)
# ----------------------------
@app.get("/api/live-status")
def live_status():
    # 1) Read sensor
    hit, cpu, ram, source = read_server_hit()

    # 2) Decide + transition
    decision = transition_state(hit)

    state = decision["state"]
    severity = decision["severity"]
    actions = decision["actions"]

    # 3) Alert message logic
    alert_message = "System Normal"

    if state == STATE_WARNING:
        alert_message = "⚠ Company Warning Triggered"

    elif state == STATE_FAN_ON:
        alert_message = "🌀 Fan Activated"

    elif state == STATE_FULL_COOLING:
        alert_message = "❄ Full Cooling System Active"

    elif state == STATE_DATA_SHIFT_GRADUAL:
        alert_message = "📦 Gradual Data Shift In Progress"

    elif state == STATE_DATA_SHIFT_FAST:
        alert_message = "🚚 Fast Data Shift In Progress"

    elif state == STATE_EMERGENCY_SHUTDOWN:
        alert_message = "🚨 Emergency Shutdown Initiated"

    # 4) Emit alert (event)
    if state != STATE_MONITOR:
        emit_alert(
            hit=hit,
            state=state,
            severity=severity,
            message=alert_message,
            source=source
        )

    # 5) Final response (LIVE SCREEN CONTRACT)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "cpu": cpu,
        "ram": ram,
        "hit": hit,
        "state": state,
        "severity": severity,
        "actions": actions,
        "alert_message": alert_message,
        "display_target": "SERVER_TEAM_SCREEN"
    }

# ----------------------------
# ALERT HISTORY API
# ----------------------------
@app.get("/api/alerts")
def get_alerts():
    return {
        "count": len(ALERT_HISTORY),
        "alerts": ALERT_HISTORY
    }

# ----------------------------
# ACK ALERT
# ----------------------------
class AckRequest(BaseModel):
    user: str = "operator"

@app.post("/api/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, req: AckRequest):
    ok = acknowledge_alert(alert_id, req.user)
    if not ok:
        raise HTTPException(status_code=404, detail="Alert not found or already handled")
    return {"status": "ACKNOWLEDGED"}

# ----------------------------
# RESOLVE ALERT
# ----------------------------
@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert_api(alert_id: int):
    ok = resolve_alert(alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "RESOLVED"}
from fastapi.responses import HTMLResponse

# ----------------------------
# LIVE STATUS SCREEN
# ----------------------------
@app.get("/live-screen", response_class=HTMLResponse)
def live_screen():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="10">
    <title>Live Server Status</title>
    <style>
        body { background:#020617; color:#e5e7eb; font-family:Arial; padding:20px; }
        h1 { color:#38bdf8; }
        .card { background:#111827; padding:16px; border-radius:10px; }
        .GREEN { color:#4ade80; }
        .YELLOW { color:#fde047; }
        .ORANGE { color:#fb923c; }
        .RED { color:#f87171; }
        .CRITICAL { color:#f43f5e; }
        .BLACK { color:#000; background:#f87171; padding:6px; }
        .label { font-weight:bold; }
    </style>
</head>
<body>
    <h1>🖥️ Live Server Status (Auto refresh 10s)</h1>
    <div class="card" id="status">Loading...</div>

<script>
fetch('/api/live-status')
.then(r => r.json())
.then(d => {
    document.getElementById('status').innerHTML = `
        <p><span class="label">Source:</span> ${d.source}</p>
        <p><span class="label">CPU:</span> ${d.cpu}</p>
        <p><span class="label">RAM:</span> ${d.ram}</p>
        <p><span class="label">HIT:</span> ${d.hit}%</p>
        <p><span class="label">State:</span>
            <span class="${d.severity}">${d.state}</span>
        </p>
        <p><span class="label">Severity:</span> ${d.severity}</p>
        <p><span class="label">Actions:</span> ${d.actions.join(', ')}</p>
        <hr>
        <h3>${d.alert_message}</h3>
    `;
});
</script>
</body>
</html>
"""

# ----------------------------
# ALERT HISTORY SCREEN
# ----------------------------
@app.get("/alerts-screen", response_class=HTMLResponse)
def alerts_screen():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="10">
    <title>Alert History</title>
    <style>
        body { background:#020617; color:#e5e7eb; font-family:Arial; padding:20px; }
        h1 { color:#f87171; }
        .alert {
            background:#111827;
            padding:14px;
            border-left:6px solid red;
            border-radius:8px;
            margin-bottom:12px;
        }
        .OPEN { border-color:#f87171; }
        .ACK { border-color:#38bdf8; }
        .RESOLVED { border-color:#4ade80; }
        .meta { font-size:13px; color:#94a3b8; }
    </style>
</head>
<body>
    <h1>🚨 Alert History (Auto refresh 10s)</h1>
    <div id="alerts">Loading...</div>

<script>
fetch('/api/alerts')
.then(r => r.json())
.then(d => {
    let html = '';
    d.alerts.forEach(a => {
        html += `
        <div class="alert ${a.status}">
            <b>${a.state}</b> | HIT ${a.hit}%<br>
            ${a.message}<br>
            <div class="meta">
                Severity: ${a.severity}<br>
                Source: ${a.source}<br>
                Status: ${a.status}<br>
                Time: ${a.timestamp}
            </div>
        </div>`;
    });
    document.getElementById('alerts').innerHTML =
        html || '<p>No alerts yet</p>';
});
</script>
</body>
</html>
"""

# ----------------------------
# SERVER REGISTRY (IN-MEMORY)
# ----------------------------
# Structure:
# SERVERS[server_id] = {
#   "memory": SYSTEM_MEMORY-like dict,
#   "alerts": [],
#   "last_seen": timestamp
# }

SERVERS = {}

def _init_server(server_id: str):
    if server_id not in SERVERS:
        SERVERS[server_id] = {
            "memory": {
                "current_state": STATE_MONITOR,
                "data_shift_started": False,
                "shutdown_initiated": False
            },
            "alerts": [],
            "last_seen": datetime.utcnow().isoformat()
        }

def _get_server_memory(server_id: str):
    _init_server(server_id)
    SERVERS[server_id]["last_seen"] = datetime.utcnow().isoformat()
    return SERVERS[server_id]["memory"]

def _get_server_alerts(server_id: str):
    _init_server(server_id)
    return SERVERS[server_id]["alerts"]

# ----------------------------
# PER-SERVER TRANSITION
# ----------------------------
def transition_state_for_server(server_id: str, hit: int):
    mem = _get_server_memory(server_id)

    # shutdown lock
    if mem["shutdown_initiated"]:
        return {
            "state": STATE_EMERGENCY_SHUTDOWN,
            "severity": SEVERITY_BLACK,
            "actions": [ACTION_EMERGENCY_SHUTDOWN],
            "locked": True
        }

    decision = decide_state_from_hit(hit)
    new_state = decision["state"]

    # data shift lock
    if new_state in (STATE_DATA_SHIFT_GRADUAL, STATE_DATA_SHIFT_FAST):
        mem["data_shift_started"] = True

    if mem["data_shift_started"] and new_state in (
        STATE_MONITOR, STATE_WARNING, STATE_FAN_ON, STATE_FULL_COOLING
    ):
        new_state = STATE_DATA_SHIFT_GRADUAL
        decision = decide_state_from_hit(THRESH_DATA_SHIFT_GRADUAL)

    if new_state == STATE_EMERGENCY_SHUTDOWN:
        mem["shutdown_initiated"] = True

    mem["current_state"] = new_state

    return {
        "state": new_state,
        "severity": decision["severity"],
        "actions": decision["actions"],
        "locked": mem["shutdown_initiated"]
    }

# ----------------------------
# MULTI-SERVER LIVE STATUS API
# ----------------------------
@app.get("/api/{server_id}/live-status")
def live_status_for_server(server_id: str):
    hit, cpu, ram, source = read_server_hit()

    decision = transition_state_for_server(server_id, hit)

    state = decision["state"]
    severity = decision["severity"]
    actions = decision["actions"]

    alert_message = "System Normal"

    if state == STATE_WARNING:
        alert_message = "⚠ Company Warning Triggered"
    elif state == STATE_FAN_ON:
        alert_message = "🌀 Fan Activated"
    elif state == STATE_FULL_COOLING:
        alert_message = "❄ Full Cooling Active"
    elif state == STATE_DATA_SHIFT_GRADUAL:
        alert_message = "📦 Gradual Data Shift In Progress"
    elif state == STATE_DATA_SHIFT_FAST:
        alert_message = "🚚 Fast Data Shift In Progress"
    elif state == STATE_EMERGENCY_SHUTDOWN:
        alert_message = "🚨 Emergency Shutdown Initiated"

    # emit alert per server
    server_alerts = _get_server_alerts(server_id)
    if state != STATE_MONITOR:
        alert = emit_alert(
            hit=hit,
            state=state,
            severity=severity,
            message=alert_message,
            source=source
        )
        if alert:
            server_alerts.insert(0, alert)

    return {
        "server_id": server_id,
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "cpu": cpu,
        "ram": ram,
        "hit": hit,
        "state": state,
        "severity": severity,
        "actions": actions,
        "alert_message": alert_message,
        "display_target": "SERVER_TEAM_SCREEN"
    }

# ----------------------------
# LIST SERVERS
# ----------------------------
@app.get("/api/servers")
def list_servers():
    return {
        "count": len(SERVERS),
        "servers": [
            {
                "server_id": sid,
                "last_seen": data["last_seen"],
                "current_state": data["memory"]["current_state"]
            }
            for sid, data in SERVERS.items()
        ]
    }
import sqlite3
import os

DB_FILE = "smart_heat_engine.db"

# ----------------------------
# DB CONNECTION
# ----------------------------
def _get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

# ----------------------------
# DB MIGRATION (AUTO)
# ----------------------------
def init_db():
    conn = _get_db()
    cur = conn.cursor()

    # Alerts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id TEXT,
        timestamp TEXT,
        hit INTEGER,
        state TEXT,
        severity TEXT,
        message TEXT,
        source TEXT,
        status TEXT,
        ack_by TEXT,
        ack_time TEXT,
        resolved_time TEXT
    )
    """)

    # Live status table (one row per server)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_status (
        server_id TEXT PRIMARY KEY,
        timestamp TEXT,
        cpu REAL,
        ram REAL,
        hit INTEGER,
        state TEXT,
        severity TEXT,
        data_shift_started INTEGER,
        shutdown_initiated INTEGER
    )
    """)

    # Servers registry
    cur.execute("""
    CREATE TABLE IF NOT EXISTS servers (
        server_id TEXT PRIMARY KEY,
        last_seen TEXT,
        current_state TEXT
    )
    """)

    conn.commit()
    conn.close()

# Initialize DB at startup
init_db()

# ----------------------------
# DB WRITE HELPERS
# ----------------------------
def db_save_alert(alert: dict, server_id: str):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO alerts
    (server_id, timestamp, hit, state, severity, message, source, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        server_id,
        alert["timestamp"],
        alert["hit"],
        alert["state"],
        alert["severity"],
        alert["message"],
        alert["source"],
        alert["status"]
    ))
    conn.commit()
    conn.close()

def db_update_live_status(server_id: str, cpu, ram, hit, state, severity, mem):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO live_status
    (server_id, timestamp, cpu, ram, hit, state, severity,
     data_shift_started, shutdown_initiated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        server_id,
        datetime.utcnow().isoformat(),
        cpu,
        ram,
        hit,
        state,
        severity,
        int(mem["data_shift_started"]),
        int(mem["shutdown_initiated"])
    ))
    conn.commit()
    conn.close()

def db_update_server_registry(server_id: str, mem):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO servers
    (server_id, last_seen, current_state)
    VALUES (?, ?, ?)
    """, (
        server_id,
        datetime.utcnow().isoformat(),
        mem["current_state"]
    ))
    conn.commit()
    conn.close()
