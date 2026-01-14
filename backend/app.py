from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import random, time
from datetime import datetime
import sqlite3

# =====================================================
# DATABASE (SQLite – permanent)
# =====================================================
DB_FILE = "alerts.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            hit INTEGER,
            state TEXT,
            severity TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_alert_db(hit, state, severity):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (time, hit, state, severity) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), hit, state, severity)
    )
    conn.commit()
    conn.close()

def fetch_alerts():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT time, hit, state, severity FROM alerts ORDER BY id DESC LIMIT 100"
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {"time": r[0], "hit": r[1], "state": r[2], "severity": r[3]}
        for r in rows
    ]

init_db()

# =====================================================
# FASTAPI APP
# =====================================================
app = FastAPI(
    title="Smart Heat Engine API",
    version="FINAL-CLEAN",
    description="API + Static UI (Live / Alerts / Servers)"
)

# =====================================================
# STATIC UI (🔥 IMPORTANT FIX)
# =====================================================
# templates/alerts_history.html
# templates/live_screen.html
# templates/servers_screen.html
app.mount("/ui", StaticFiles(directory="templates"), name="ui")

# =====================================================
# CONFIG
# =====================================================
MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75

FREEZE_THRESHOLD = 90
RELEASE_THRESHOLD = 70

# =====================================================
# SENSOR (SIMULATION)
# =====================================================
def read_sensor():
    for _ in range(MAX_RETRIES):
        try:
            if random.random() < 0.3:
                raise Exception()
            return random.randint(30, 95), False
        except:
            time.sleep(RETRY_DELAY)
    return FAILSAFE_DEFAULT_HIT, True

# =====================================================
# CORE LOGIC
# =====================================================
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

# =====================================================
# MULTI SERVER REGISTRY (SCALABLE)
# =====================================================
SERVERS = {
    f"server-{i}": {"freeze": False, "hit": 0}
    for i in range(1, 4)
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

# =====================================================
# BASIC ROUTES
# =====================================================
@app.get("/")
def root():
    return {
        "message": "Smart Heat Engine running 🚀",
        "ui": {
            "live": "/ui/live_screen.html",
            "alerts": "/ui/alerts_history.html",
            "servers": "/ui/servers_screen.html"
        }
    }

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

# =====================================================
# PER SERVER LIVE STATUS
# =====================================================
@app.get("/api/server/{server_id}/live-status")
def server_status(server_id: str):
    if server_id not in SERVERS:
        return {"error": "Unknown server"}

    hit, failsafe = read_sensor()
    result = analyze_hit(hit)

    SERVERS[server_id]["hit"] = hit
    update_server_freeze(server_id, hit)

    if hit >= 75:
        save_alert_db(hit, result["state"], result["severity"])

    return {
        "server_id": server_id,
        "hit": hit,
        "freeze": SERVERS[server_id]["freeze"],
        "state": result["state"],
        "severity": result["severity"],
        "actions": result["actions"],
    }

# =====================================================
# GLOBAL LIVE STATUS
# =====================================================
@app.get("/api/live-status")
def global_live_status():
    target = choose_target_server()

    if not target:
        return {
            "server_id": "NONE",
            "hit": 100,
            "freeze": True,
            "state": "ALL_SERVERS_FROZEN",
            "severity": "CRITICAL",
            "actions": []
        }

    return server_status(target)

# =====================================================
# ROUTER STATUS
# =====================================================
@app.get("/api/router/status")
def router_status():
    target = choose_target_server()
    return {
        "next_target_server": target,
        "reason": "Lowest load active server" if target else "ALL SERVERS FROZEN"
    }

# =====================================================
# ALERT HISTORY API
# =====================================================
@app.get("/api/alerts/history")
def alert_history():
    alerts = fetch_alerts()
    return {"count": len(alerts), "alerts": alerts}