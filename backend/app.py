from fastapi import FastAPI
from pydantic import BaseModel
import random
import time
from datetime import datetime
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Smart Heat Engine API",
    version="FINAL",
    description="Retry + Fail-Safe + Live Screen + Alert History + FREEZE"
)

# -----------------------------
# CONFIG
# -----------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75
MAX_ALERTS = 100

FREEZE_THRESHOLD = 90
FREEZE_RELEASE = 70

# -----------------------------
# SYSTEM MEMORY
# -----------------------------
SYSTEM_STATE = {
    "freeze": False
}

# -----------------------------
# ALERT HISTORY
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

# -----------------------------
# SENSOR SIM
# -----------------------------
def read_sensor():
    for _ in range(MAX_RETRIES):
        try:
            if random.random() < 0.3:
                raise Exception()
            return random.randint(30, 95), False
        except:
            time.sleep(RETRY_DELAY)

    return FAILSAFE_DEFAULT_HIT, True

# -----------------------------
# ALERT SAVE
# -----------------------------
def save_alert(hit, result):
    ALERT_HISTORY.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "hit": hit,
        "state": result["state"],
        "severity": result["severity"],
        "message": "HIGH SERVER LOAD",
    })
    if len(ALERT_HISTORY) > MAX_ALERTS:
        ALERT_HISTORY.pop(0)

# -----------------------------
# API ROUTES
# -----------------------------
@app.get("/")
def root():
    return {"message": "Smart Heat Engine running 🚀"}

@app.get("/api/live-status")
def live_status():
    hit, failsafe = read_sensor()

    # FREEZE LOGIC
    if hit >= FREEZE_THRESHOLD:
        SYSTEM_STATE["freeze"] = True
    elif SYSTEM_STATE["freeze"] and hit <= FREEZE_RELEASE:
        SYSTEM_STATE["freeze"] = False

    result = analyze_hit(hit)

    if hit >= 75:
        save_alert(hit, result)

    return {
        "hit": hit,
        "failsafe": failsafe,
        "freeze": SYSTEM_STATE["freeze"],
        "state": result["state"],
        "severity": result["severity"],
        "actions": result["actions"],
        "alert_message": (
            "🚨 SERVER FREEZED – TRAFFIC REDIRECTED"
            if SYSTEM_STATE["freeze"]
            else "System Normal"
        )
    }

@app.get("/api/alerts/history")
def alerts():
    return {"count": len(ALERT_HISTORY), "alerts": ALERT_HISTORY}

# -----------------------------
# LIVE SCREEN (POLISHED + BLINK)
# -----------------------------
@app.get("/live-screen", response_class=HTMLResponse)
def live_screen():
    return """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="10">
<title>Live Server Status</title>

<style>
body { background:#020617; color:#e5e7eb; font-family:Arial; padding:20px }
.card {
  background:#111827; padding:20px; border-radius:12px;
  border:4px solid #1e293b; max-width:500px
}
.CRITICAL {
  animation: blink 1s infinite;
}
@keyframes blink {
  0% { border-color:red; box-shadow:0 0 15px red }
  50% { border-color:transparent; box-shadow:none }
  100% { border-color:red; box-shadow:0 0 15px red }
}
</style>
</head>

<body>
<h1>🖥 Live Server Status</h1>
<div id="card" class="card">Loading...</div>

<script>
fetch('/api/live-status')
.then(r=>r.json())
.then(d=>{
  const c=document.getElementById('card');
  c.className='card';
  if(d.severity==='CRITICAL') c.classList.add('CRITICAL');
  c.innerHTML=`
    HIT: ${d.hit}%<br>
    STATE: ${d.state}<br>
    SEVERITY: ${d.severity}<br>
    FREEZE: ${d.freeze}<br>
    ACTIONS: ${d.actions.join(', ')}<br><br>
    <b>${d.alert_message}</b>
  `;
});
</script>
</body>
</html>
"""
# =====================================================
# MULTI SERVER REGISTRY (IN-MEMORY)
# =====================================================

SERVERS = {
    "server-1": {
        "freeze": False,
        "hit": 0,
        "last_update": None
    },
    "server-2": {
        "freeze": False,
        "hit": 0,
        "last_update": None
    },
    "server-3": {
        "freeze": False,
        "hit": 0,
        "last_update": None
    }
}

FREEZE_THRESHOLD = 90
RELEASE_THRESHOLD = 70


# =====================================================
# FREEZE / RELEASE LOGIC
# =====================================================

def update_server_freeze(server_id: str, hit: int):
    server = SERVERS[server_id]

    # FREEZE
    if hit >= FREEZE_THRESHOLD:
        server["freeze"] = True

    # RELEASE
    elif hit <= RELEASE_THRESHOLD:
        server["freeze"] = False


# =====================================================
# LOAD ROUTER (LOGICAL)
# =====================================================

def choose_target_server():
    """
    Returns server_id where load can be sent.
    Chooses lowest HIT non-frozen server.
    """
    active_servers = {
        sid: s for sid, s in SERVERS.items() if not s["freeze"]
    }

    if not active_servers:
        return None

    return min(active_servers, key=lambda s: active_servers[s]["hit"])


# =====================================================
# MULTI SERVER LIVE STATUS API
# =====================================================

@app.get("/api/server/{server_id}/live-status")
def live_status_for_server(server_id: str):
    if server_id not in SERVERS:
        return {"error": "Unknown server"}

    hit, failsafe = read_sensor_with_retry()
    result = analyze_hit(hit)

    # Update server state
    SERVERS[server_id]["hit"] = hit
    SERVERS[server_id]["last_update"] = datetime.now().isoformat()

    update_server_freeze(server_id, hit)

    # Save alert if needed
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
        "message": (
            "🚫 SERVER FROZEN – TRAFFIC REDIRECTED"
            if SERVERS[server_id]["freeze"]
            else "System Normal"
        ),
        "display_target": "SERVER_TEAM_SCREEN"
    }


# =====================================================
# SERVER LIST (DASHBOARD SUPPORT)
# =====================================================

@app.get("/api/servers")
def list_servers():
    return {
        "count": len(SERVERS),
        "servers": SERVERS
    }


# =====================================================
# ROUTER STATUS (WHERE NEW REQUESTS WILL GO)
# =====================================================

@app.get("/api/router/status")
def router_status():
    target = choose_target_server()

    return {
        "next_target_server": target,
        "reason": (
            "Lowest load active server selected"
            if target else
            "⚠ ALL SERVERS FROZEN – HOLD REQUESTS"
        )
    }@app.get("/api/ping")
def ping():
    return {"status": "ok"}
# =====================================================
# MULTI SERVER SUPPORT (FIXED VERSION)
# =====================================================

SERVERS = {
    "server-1": {"freeze": False, "hit": 0, "last_update": None},
    "server-2": {"freeze": False, "hit": 0, "last_update": None},
    "server-3": {"freeze": False, "hit": 0, "last_update": None},
}

FREEZE_THRESHOLD = 90
RELEASE_THRESHOLD = 70


def update_server_freeze(server_id: str, hit: int):
    if hit >= FREEZE_THRESHOLD:
        SERVERS[server_id]["freeze"] = True
    elif hit <= RELEASE_THRESHOLD:
        SERVERS[server_id]["freeze"] = False


def choose_target_server():
    active = {k: v for k, v in SERVERS.items() if not v["freeze"]}
    if not active:
        return None
    return min(active, key=lambda s: active[s]["hit"])


@app.get("/api/server/{server_id}/live-status")
def live_status_for_server(server_id: str):
    if server_id not in SERVERS:
        return {"error": "Unknown server"}

    # ✅ FIXED SENSOR CALL
    hit, failsafe = read_sensor()

    result = analyze_hit(hit)

    SERVERS[server_id]["hit"] = hit
    SERVERS[server_id]["last_update"] = datetime.now().isoformat()

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
        "message": (
            "🚫 SERVER FROZEN – TRAFFIC REDIRECTED"
            if SERVERS[server_id]["freeze"]
            else "System Normal"
        ),
        "display_target": "SERVER_TEAM_SCREEN"
    }


@app.get("/api/servers")
def list_servers():
    return {
        "count": len(SERVERS),
        "servers": SERVERS
    }


@app.get("/api/router/status")
def router_status():
    target = choose_target_server()
    return {
        "next_target_server": target,
        "reason": (
            "Lowest load active server selected"
            if target
            else "⚠ ALL SERVERS FROZEN – HOLD REQUESTS"
        )
    }