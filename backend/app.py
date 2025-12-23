from fastapi import FastAPI
from pydantic import BaseModel
import random
import time

app = FastAPI(
    title="Smart Heat Engine API",
    version="1.0",
    description="Retry + Fail-Safe enabled control system"
)

# -----------------------------
# CONFIG
# -----------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
FAILSAFE_DEFAULT_HIT = 75  # assume danger if unknown

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
        return {
            "state": "MONITOR",
            "severity": "GREEN",
            "actions": []
        }

    elif hit < 65:
        return {
            "state": "WARNING",
            "severity": "YELLOW",
            "actions": ["notify_company"]
        }

    elif hit < 70:
        return {
            "state": "FAN_ON",
            "severity": "ORANGE",
            "actions": ["fan_on"]
        }

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

# -----------------------------
# RETRY + FAIL-SAFE SENSOR SIM
# -----------------------------
def read_sensor_with_retry():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # simulate sensor read (random failure)
            if random.random() < 0.3:
                raise Exception("Sensor timeout")

            hit = random.randint(30, 95)
            return hit, False  # success, not failsafe

        except Exception as e:
            print(f"[Retry {attempt}] Sensor error:", e)
            time.sleep(RETRY_DELAY)

    # FAIL-SAFE MODE
    print("⚠ FAIL-SAFE ACTIVATED")
    return FAILSAFE_DEFAULT_HIT, True

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
    return {
        "hit": input.hit,
        **result
    }

@app.get("/api/simulate")
def simulate():
    hit, failsafe = read_sensor_with_retry()
    result = analyze_hit(hit)

    return {
        "hit": hit,
        "failsafe": failsafe,
        **result
    }
# -----------------------------
# LIVE SCREEN STATUS (FOR SERVER TEAM)
# -----------------------------
@app.get("/api/live-status")
def live_status():
    hit, failsafe = read_sensor_with_retry()
    analysis = analyze_hit(hit)

    alert = False
    alert_message = "System Normal"

    if hit >= 75:
        alert = True
        alert_message = "⚠ HIGH SERVER LOAD – IMMEDIATE ATTENTION REQUIRED"

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