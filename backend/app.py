from fastapi import FastAPI
from pydantic import BaseModel
import random
import time
from datetime import datetime

app = FastAPI(
    title="Smart Heat Engine API",
    version="1.2",
    description="Retry + Fail-Safe + Live Screen + Alert History"
)

# -----------------------------
# CONFIG
# -----------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
FAILSAFE_DEFAULT_HIT = 75

MAX_ALERTS = 100

# -----------------------------
# ALERT HISTORY (IN-MEMORY)
# -----------------------------
ALERT_HISTORY = []

# -----------------------------
# DATA MODEL
# -----------------------------
class HitInput(BaseModel):
    hit: int

# -----------------------------
# CORE LOGIC
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
    elif hit < 80:
        return {
            "state": "GRADUAL_DATA_SHIFT",
            "severity": "RED",
            "actions": [
                "fan_on", "fan_speed_high",
                "cooling_system_on", "data_shift_gradual"
            ]
        }
    elif hit < 90:
        return {
            "state": "FAST_DATA_SHIFT",
            "severity": "CRITICAL",
            "actions": [
                "fan_on", "fan_speed_high",
                "cooling_system_on", "data_shift_fast"
            ]
        }
    else:
        return {
            "state": "EMERGENCY_SHUTDOWN",
            "severity": "BLACK",
            "actions": ["shutdown_server"]
        }

# -----------------------------
# RETRY + FAIL-SAFE SENSOR SIM
# -----------------------------
def read_sensor_with_retry():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if random.random() < 0.3:
                raise Exception("Sensor timeout")

            hit = random.randint(30, 95)
            return hit, False

        except Exception:
            time.sleep(RETRY_DELAY)

    return FAILSAFE_DEFAULT_HIT, True

# -----------------------------
# SAVE ALERT
# -----------------------------
def save_alert(hit, result):
    alert = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hit": hit,
        "state": result["state"],
        "severity": result["severity"],
        "message": "HIGH SERVER LOAD - IMMEDIATE ATTENTION REQUIRED",
        "display_target": "SERVER_TEAM_SCREEN"
    }

    ALERT_HISTORY.append(alert)
    if len(ALERT_HISTORY) > MAX_ALERTS:
        ALERT_HISTORY.pop(0)

# -----------------------------
# ROUTES
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
        "mode": "retry + fail-safe",
        "status": "active"
    }

@app.post("/api/analyze")
def analyze(input: HitInput):
    result = analyze_hit(input.hit)
    if input.hit >= 75:
        save_alert(input.hit, result)
    return {"hit": input.hit, **result}

@app.get("/api/simulate")
def simulate():
    hit, failsafe = read_sensor_with_retry()
    result = analyze_hit(hit)
    if hit >= 75:
        save_alert(hit, result)
    return {"hit": hit, "failsafe": failsafe, **result}

# -----------------------------
# LIVE SCREEN STATUS (SERVER TEAM)
# -----------------------------
from fastapi.responses import HTMLResponse

@app.get("/live-screen", response_class=HTMLResponse)
def live_screen():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="10">
    <title>Live Server Status</title>

    <style>
        body {
            background: #020617;
            color: #e5e7eb;
            font-family: Arial, sans-serif;
            padding: 20px;
        }

        h1 {
            color: #38bdf8;
        }

        .status-card {
            background: #111827;
            padding: 20px;
            border-radius: 12px;
            border: 3px solid transparent;
            max-width: 500px;
        }

        .label {
            font-weight: bold;
            color: #94a3b8;
        }

        .GREEN { color: #4ade80; }
        .YELLOW { color: #fde047; }
        .ORANGE { color: #fb923c; }
        .RED { color: #f87171; }
        .CRITICAL { color: #ef4444; }

        /* ===== BLINK ANIMATIONS ===== */
        @keyframes critical-blink {
            0%   { border-color: #ef4444; box-shadow: 0 0 12px #ef4444; }
            50%  { border-color: transparent; box-shadow: none; }
            100% { border-color: #ef4444; box-shadow: 0 0 12px #ef4444; }
        }

        @keyframes text-blink {
            0%   { opacity: 1; }
            50%  { opacity: 0.3; }
            100% { opacity: 1; }
        }

        .status-card.CRITICAL {
            animation: critical-blink 1s infinite;
        }

        .alert-text.CRITICAL {
            animation: text-blink 1s infinite;
            font-weight: bold;
        }
    </style>
</head>

<body>
    <h1>🖥️ Live Server Status (Auto refresh 10s)</h1>

    <div id="statusCard" class="status-card">
        <p><span class="label">HIT:</span> <span id="hitVal">--</span>%</p>
        <p><span class="label">State:</span> <span id="stateText">--</span></p>
        <p><span class="label">Severity:</span> <span id="severityText">--</span></p>
        <p><span class="label">Actions:</span> <span id="actionsText">--</span></p>
        <hr>
        <p id="alertText" class="alert-text">Loading...</p>
    </div>

<script>
fetch('/api/live-status')
.then(res => res.json())
.then(d => {

    const card = document.getElementById("statusCard");
    const alertText = document.getElementById("alertText");

    document.getElementById("hitVal").innerText = d.hit;
    document.getElementById("stateText").innerText = d.state;
    document.getElementById("severityText").innerText = d.severity;
    document.getElementById("actionsText").innerText = d.actions.join(', ');
    alertText.innerText = d.alert_message;

    card.classList.remove("CRITICAL");
    alertText.classList.remove("CRITICAL");

    if (d.severity === "CRITICAL") {
        card.classList.add("CRITICAL");
        alertText.classList.add("CRITICAL");
    }
});
</script>

</body>
</html>
"""
# -----------------------------
# ALERT HISTORY API
# -----------------------------
@app.get("/api/alerts/history")
def get_alert_history():
    return {
        "count": len(ALERT_HISTORY),
        "alerts": ALERT_HISTORY
    }
from fastapi.responses import HTMLResponse

@app.get("/live-screen", response_class=HTMLResponse)
def live_screen():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="10">
    <title>LIVE SERVER STATUS</title>
</head>
<body style="background:black;color:white;font-family:Arial">
    <h1>LIVE SERVER STATUS</h1>
    <div id="data">Loading...</div>

<script>
fetch('/api/live-status')
.then(r => r.json())
.then(d => {
    document.getElementById('data').innerHTML = `
        HIT: ${d.hit}<br>
        STATE: ${d.state}<br>
        SEVERITY: ${d.severity}<br>
        ACTIONS: ${d.actions.join(', ')}<br>
        MESSAGE: ${d.alert_message}
    `;
});
</script>
</body>
</html>
"""