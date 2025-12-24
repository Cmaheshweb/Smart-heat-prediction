from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
import random
import time

app = FastAPI(
    title="Smart Heat Engine API",
    version="1.0",
    description="Retry + Fail-Safe + Live Alert System"
)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75
MAX_ALERTS = 100

# --------------------------------------------------
# GLOBAL ALERT HISTORY
# --------------------------------------------------
ALERT_HISTORY = []

# --------------------------------------------------
# DATA MODEL
# --------------------------------------------------
class HitInput(BaseModel):
    hit: int

# --------------------------------------------------
# CORE ANALYSIS LOGIC
# --------------------------------------------------
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
                "fan_on",
                "fan_speed_high",
                "cooling_system_on",
                "data_shift_gradual"
            ]
        }

    elif hit < 90:
        return {
            "state": "FAST_DATA_SHIFT",
            "severity": "CRITICAL",
            "actions": [
                "fan_on",
                "fan_speed_high",
                "cooling_system_on",
                "data_shift_fast"
            ]
        }

    else:
        return {
            "state": "EMERGENCY_SHUTDOWN",
            "severity": "BLACK",
            "actions": ["shutdown_server"]
        }

# --------------------------------------------------
# RETRY + FAIL-SAFE SENSOR SIMULATION
# --------------------------------------------------
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

# --------------------------------------------------
# ALERT STORE
# --------------------------------------------------
def store_alert(hit, analysis, message):
    ALERT_HISTORY.append({
        "time": datetime.utcnow().isoformat(),
        "hit": hit,
        "state": analysis["state"],
        "severity": analysis["severity"],
        "message": message
    })

    if len(ALERT_HISTORY) > MAX_ALERTS:
        ALERT_HISTORY.pop(0)

# --------------------------------------------------
# BASIC ROUTES
# --------------------------------------------------
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
    analysis = analyze_hit(input.hit)
    return {"hit": input.hit, **analysis}

# --------------------------------------------------
# LIVE STATUS (SERVER TEAM SCREEN)
# --------------------------------------------------
@app.get("/api/live-status")
def live_status():
    hit, failsafe = read_sensor_with_retry()
    analysis = analyze_hit(hit)

    alert = False
    alert_message = "System Normal"

    if hit >= 75:
        alert = True
        alert_message = "⚠ HIGH SERVER LOAD – IMMEDIATE ATTENTION REQUIRED"
        store_alert(hit, analysis, alert_message)

    return {
        "hit": hit,
        "failsafe": failsafe,
        "state": analysis["state"],
        "severity": analysis["severity"],
        "actions": analysis["actions"],
        "alert": alert,
        "alert_message": alert_message,
        "display_target": "SERVER_TEAM_SCREEN"
    }

# --------------------------------------------------
# ALERT HISTORY API
# --------------------------------------------------
@app.get("/api/alerts")
def alert_history():
    return {
        "count": len(ALERT_HISTORY),
        "alerts": ALERT_HISTORY[::-1]
    }

# --------------------------------------------------
# LIVE ALERT SCREEN (AUTO REFRESH 10s)
# --------------------------------------------------
@app.get("/alerts-screen", response_class=HTMLResponse)
def alerts_screen():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Server Alert Screen</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {
            background:#0f172a;
            color:#e5e7eb;
            font-family:Arial;
            padding:20px;
        }
        h1 { color:#38bdf8; }
        .alert {
            background:#1e293b;
            padding:10px;
            margin-bottom:10px;
            border-left:6px solid red;
        }
        .GREEN { border-color:green; }
        .YELLOW { border-color:yellow; }
        .ORANGE { border-color:orange; }
        .RED { border-color:red; }
        .BLACK { border-color:black; }
        small { color:#94a3b8; }
    </style>
</head>
<body>

<h1>🚨 Server Alert History (Auto Refresh 10s)</h1>
<div id="alerts">Loading...</div>

<script>
async function loadAlerts(){
    const res = await fetch('/api/alerts');
    const data = await res.json();
    let html = '';
    data.alerts.forEach(a=>{
        html += `
        <div class="alert ${a.severity}">
            <b>${a.state}</b> | HIT: ${a.hit}<br>
            ${a.message}<br>
            <small>${a.time}</small>
        </div>`;
    });
    document.getElementById('alerts').innerHTML = html || "No alerts yet";
}
loadAlerts();
</script>

</body>
</html>
"""