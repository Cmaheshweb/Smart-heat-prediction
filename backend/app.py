from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import random, time
from datetime import datetime

app = FastAPI(
    title="Smart Heat Engine API",
    version="FINAL-STABLE",
    description="Live Heat Control + Freeze + Multi-Server + Blink"
)

# =====================================================
# CONFIG
# =====================================================
MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75
MAX_ALERTS = 100

FREEZE_THRESHOLD = 90
RELEASE_THRESHOLD = 70

# =====================================================
# ALERT HISTORY
# =====================================================
ALERT_HISTORY = []

# =====================================================
# SENSOR (SIM)
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
        return {"state": "FULL_COOLING", "severity": "RED",
                "actions": ["fan_on", "fan_speed_high", "cooling_system_on"]}
    elif hit < 80:
        return {"state": "GRADUAL_DATA_SHIFT", "severity": "RED",
                "actions": ["fan_on", "fan_speed_high", "cooling_system_on", "data_shift_gradual"]}
    elif hit < 90:
        return {"state": "FAST_DATA_SHIFT", "severity": "CRITICAL",
                "actions": ["fan_on", "fan_speed_high", "cooling_system_on", "data_shift_fast"]}
    else:
        return {"state": "FREEZE", "severity": "CRITICAL",
                "actions": ["freeze_incoming_requests", "route_to_standby"]}

def save_alert(hit, result):
    ALERT_HISTORY.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "hit": hit,
        "state": result["state"],
        "severity": result["severity"]
    })
    if len(ALERT_HISTORY) > MAX_ALERTS:
        ALERT_HISTORY.pop(0)

# =====================================================
# BASIC ROUTES
# =====================================================
@app.get("/")
def root():
    return {"message": "Smart Heat Engine running 🚀"}

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/alerts/history")
def alerts():
    return {"count": len(ALERT_HISTORY), "alerts": ALERT_HISTORY}

# =====================================================
# MULTI SERVER REGISTRY
# =====================================================
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
    active = {k:v for k,v in SERVERS.items() if not v["freeze"]}
    if not active:
        return None
    return min(active, key=lambda s: active[s]["hit"])

# =====================================================
# SINGLE (GLOBAL) LIVE STATUS  ✅ FIX 1
# =====================================================
@app.get("/api/live-status")
def global_live_status():
    return server_status("server-1")

# =====================================================
# MULTI SERVER LIVE STATUS
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
        save_alert(hit, result)

    return {
        "server_id": server_id,
        "hit": hit,
        "freeze": SERVERS[server_id]["freeze"],
        "state": result["state"],
        "severity": result["severity"],
        "actions": result["actions"],
    }

@app.get("/api/servers")
def list_servers():
    return SERVERS

@app.get("/api/router/status")
def router_status():
    target = choose_target_server()
    return {
        "next_target_server": target,
        "reason": "Lowest load active server" if target else "ALL SERVERS FROZEN"
    }

# =====================================================
# LIVE SCREEN (STRONG BLINK)  ✅ FIX 2
# =====================================================
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
  background:#020617;
  color:#e5e7eb;
  font-family:Arial;
}
.card {
  background:#111827;
  padding:20px;
  border-radius:12px;
  border:4px solid #1e293b;
  width:320px;
}
.CRITICAL {
  animation: blink 1s infinite;
  border-color:red;
  box-shadow:0 0 20px red;
}
@keyframes blink {
  0% { opacity:1 }
  50% { opacity:0.3 }
  100% { opacity:1 }
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
    <b>SERVER:</b> ${d.server_id || 'server-1'}<br>
    <b>HIT:</b> ${d.hit}%<br>
    <b>STATE:</b> ${d.state}<br>
    <b>SEVERITY:</b> ${d.severity}<br>
    <b>FREEZE:</b> ${d.freeze}
  `;
});
</script>
</body>
</html>
"""