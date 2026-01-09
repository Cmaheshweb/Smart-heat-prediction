from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import random, time
from datetime import datetime

# ==============================
# DATABASE
# ==============================
from alerts_db import init_db, save_alert_db, fetch_alerts

# ==============================
# APP INIT
# ==============================
app = FastAPI(
    title="Smart Heat Engine API",
    version="FINAL-STABLE",
    description="Live Heat Control + Freeze + Multi-Server + Permanent Alert History"
)

init_db()

# ==============================
# CONFIG
# ==============================
MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75

FREEZE_THRESHOLD = 90
RELEASE_THRESHOLD = 70

# ==============================
# SENSOR (SIMULATION)
# ==============================
def read_sensor():
    for _ in range(MAX_RETRIES):
        try:
            if random.random() < 0.3:
                raise Exception()
            return random.randint(30, 95), False
        except:
            time.sleep(RETRY_DELAY)
    return FAILSAFE_DEFAULT_HIT, True

# ==============================
# CORE STATE LOGIC (LOCKED)
# ==============================
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
            "actions": ["fan_on", "fan_speed_high", "cooling_system_on", "data_shift_gradual"]
        }
    elif hit < 90:
        return {
            "state": "FAST_DATA_SHIFT",
            "severity": "CRITICAL",
            "actions": ["fan_on", "fan_speed_high", "cooling_system_on", "data_shift_fast"]
        }
    else:
        return {
            "state": "FREEZE",
            "severity": "CRITICAL",
            "actions": ["freeze_incoming_requests", "route_to_standby"]
        }

# ==============================
# ALERT SAVE (PERMANENT)
# ==============================
def save_alert(hit, result):
    save_alert_db(
        hit=hit,
        state=result["state"],
        severity=result["severity"],
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

# ==============================
# BASIC ROUTES
# ==============================
@app.get("/")
def root():
    return {"message": "Smart Heat Engine running 🚀"}

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/alerts/history")
def alert_history():
    alerts = fetch_alerts()
    return {"count": len(alerts), "alerts": alerts}

# ==============================
# MULTI SERVER REGISTRY (SCALABLE)
# ==============================
SERVERS = {
    "server-1": {"freeze": False, "hit": 0},
    "server-2": {"freeze": False, "hit": 0},
    "server-3": {"freeze": False, "hit": 0},
}

def update_server_freeze(server_id, hit):
    if hit >= FREEZE_THRESHOLD:
        SERVERS[server_id]["freeze"] = True
    elif hit <= RELEASE_THRESHOLD:
        SERVERS[server_id]["freeze"] = False

def choose_target_server():
    active = {k: v for k, v in SERVERS.items() if not v["freeze"]}
    if not active:
        return None
    return min(active, key=lambda s: active[s]["hit"])

# ==============================
# PER SERVER LIVE STATUS
# ==============================
@app.get("/api/server/{server_id}/live-status")
def server_live_status(server_id: str):
    if server_id not in SERVERS:
        return {"error": "Unknown server"}

    hit, failsafe = read_sensor()
    result = analyze_hit(hit)

    SERVERS[server_id]["hit"] = hit
    update_server_freeze(server_id, hit)

    if hit >= 75:
        save_alert(hit, result)

    return {
        "server_id": server_id,
        "hit": hit,
        "freeze": SERVERS[server_id]["freeze"],
        "failsafe": failsafe,
        "state": result["state"],
        "severity": result["severity"],
        "actions": result["actions"],
    }

# ==============================
# GLOBAL LIVE STATUS (AUTO ROUTE)
# ==============================
@app.get("/api/live-status")
def global_live_status():
    target = choose_target_server()
    if not target:
        return {
            "status": "ALL_SERVERS_FROZEN",
            "message": "⚠ All servers frozen – holding traffic"
        }
    return server_live_status(target)

# ==============================
# SERVER LIST
# ==============================
@app.get("/api/servers")
def list_servers():
    return SERVERS

# ==============================
# ROUTER STATUS
# ==============================
@app.get("/api/router/status")
def router_status():
    target = choose_target_server()
    return {
        "next_target_server": target,
        "reason": "Lowest load active server" if target else "ALL SERVERS FROZEN"
    }

# ==============================
# LIVE SCREEN (HTML)
# ==============================
@app.get("/live-screen", response_class=HTMLResponse)
def live_screen():
    return open("templates/live_screen.html").read()

@app.get("/alerts-screen", response_class=HTMLResponse)
def alerts_screen():
    return open("templates/alerts_screen.html").read()

@app.get("/servers-screen", response_class=HTMLResponse)
def servers_screen():
    return open("templates/servers_screen.html").read()