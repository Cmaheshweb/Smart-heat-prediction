from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Smart Heat Engine API")

# -----------------------------
# DATA MODEL
# -----------------------------
class HitInput(BaseModel):
    hit: int


# -----------------------------
# ROOT / HEALTH
# -----------------------------
@app.get("/")
def root():
    return {"message": "Smart Heat Engine API is running 🚀"}


@app.get("/api/ping")
def ping():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    return {
        "service": "smart-heat-engine",
        "state": "running"
    }


# -----------------------------
# CORE ENGINE LOGIC
# -----------------------------
@app.post("/api/analyze")
def analyze(data: HitInput):
    hit = data.hit

    if hit < 60:
        return {
            "hit": hit,
            "state": "MONITOR",
            "severity": "GREEN",
            "actions": []
        }

    elif hit < 65:
        return {
            "hit": hit,
            "state": "WARNING",
            "severity": "YELLOW",
            "actions": ["notify_company"]
        }

    elif hit < 70:
        return {
            "hit": hit,
            "state": "FAN_ON",
            "severity": "ORANGE",
            "actions": ["fan_on"]
        }

    elif hit < 75:
        return {
            "hit": hit,
            "state": "FULL_COOLING",
            "severity": "RED",
            "actions": ["fan_on", "fan_speed_high", "cooling_system_on"]
        }

    elif hit < 80:
        return {
            "hit": hit,
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
            "hit": hit,
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
            "hit": hit,
            "state": "EMERGENCY_SHUTDOWN",
            "severity": "BLACK",
            "actions": ["shutdown_server"]
        }