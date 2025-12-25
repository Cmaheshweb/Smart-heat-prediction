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
@app.get("/api/live-status")
def live_status():
    hit, failsafe = read_sensor_with_retry()
    result = analyze_hit(hit)

    alert = hit >= 75
    if alert:
        save_alert(hit, result)

    return {
        "hit": hit,
        "failsafe": failsafe,
        "state": result["state"],
        "severity": result["severity"],
        "actions": result["actions"],
        "alert": alert,
        "alert_message": (
            "⚠ HIGH SERVER LOAD – IMMEDIATE ATTENTION REQUIRED"
            if alert else "System Normal"
        ),
        "display_target": "SERVER_TEAM_SCREEN"
    }

# -----------------------------
# ALERT HISTORY API
# -----------------------------
@app.get("/api/alerts/history")
def get_alert_history():
    return {
        "count": len(ALERT_HISTORY),
        "alerts": ALERT_HISTORY
    }