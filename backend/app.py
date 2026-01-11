from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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
    version="FINAL-STABLE",
    description="Live Heat Control + Freeze + Multi-Server + Blink + Alert History"
)

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
    return {"message": "Smart Heat Engine running 🚀"}

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
# GLOBAL LIVE STATUS (ALWAYS STRUCTURED)
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
# SERVERS API (FIXED)
# =====================================================
@app.get("/api/servers")
def list_servers():
    return SERVERS

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

# =====================================================
# LIVE SCREEN
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
body { background:#020617; color:#e5e7eb; font-family:Arial; padding:20px }
.card {
  background:#111827;
  padding:20px;
  border-radius:12px;
  border:4px solid #1e293b;
  max-width:500px;
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
    <b>SERVER:</b> ${d.server_id}<br>
    <b>HIT:</b> ${d.hit}%<br>
    <b>STATE:</b> ${d.state}<br>
    <b>SEVERITY:</b> ${d.severity}<br>
    <b>FREEZE:</b> ${d.freeze}<br>
    <b>ACTIONS:</b> ${d.actions.join(', ')}
  `;
});
</script>
</body>
</html>
"""

# =====================================================
# ALERT HISTORY SCREEN
# =====================================================
@app.get("/alerts-screen", response_class=HTMLResponse)
def alerts_screen():
    return """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="10">
<title>Alert History</title>
<style>
body { background:#020617; color:#e5e7eb; font-family:Arial; padding:20px }
.alert {
  background:#111827;
  padding:12px;
  border-left:6px solid red;
  margin-bottom:10px;
  border-radius:8px;
}
.GREEN { border-color:#4ade80 }
.YELLOW { border-color:#fde047 }
.ORANGE { border-color:#fb923c }
.RED { border-color:#f87171 }
.CRITICAL { border-color:#ef4444; animation: blink 1s infinite }
@keyframes blink {
  0% { opacity:1 } 50% { opacity:0.4 } 100% { opacity:1 }
}
</style>
</head>
<body>
<h1>🚨 Alert History</h1>
<div id="alerts">Loading...</div>

<script>
fetch('/api/alerts/history')
.then(r=>r.json())
.then(d=>{
  let html='';
  d.alerts.forEach(a=>{
    html+=`
      <div class="alert ${a.severity}">
        <b>${a.state}</b> | HIT ${a.hit}%<br>
        Severity: ${a.severity}<br>
        Time: ${a.time}
      </div>`;
  });
  document.getElementById('alerts').innerHTML =
    html || '<p>No alerts yet</p>';
});
</script>
</body>
</html>
"""

# =====================================================
# SERVERS SCREEN
# =====================================================
@app.get("/servers-screen", response_class=HTMLResponse)
def servers_screen():
    return """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="10">
<title>Servers Status</title>
<style>
body { background:#020617; color:#e5e7eb; font-family:Arial; padding:20px }
.card {
  background:#111827;
  padding:14px;
  border-radius:10px;
  margin-bottom:12px;
}
.FROZEN { border-left:6px solid red }
.ACTIVE { border-left:6px solid green }
</style>
</head>
<body>
<h1>🗄 Servers Status</h1>
<div id="servers">Loading...</div>

<script>
fetch('/api/servers')
.then(r=>r.json())
.then(d=>{
  let html='';
  Object.entries(d).forEach(([id,s])=>{
    html+=`
      <div class="card ${s.freeze?'FROZEN':'ACTIVE'}">
        <b>${id}</b><br>
        HIT: ${s.hit}%<br>
        FREEZE: ${s.freeze}
      </div>`;
  });
  document.getElementById('servers').innerHTML=html;
});
</script>
</body>
</html>
"""