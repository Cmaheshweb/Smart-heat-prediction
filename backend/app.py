from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import psutil
import time
from datetime import datetime
import os

# ==================================================
# APP CONFIG
# ==================================================
app = FastAPI(
    title="Smart Heat Engine API",
    version="4.0",
    description="Live Status + Alerts + ACK/RESOLVE + SQLite (Auto Migration)"
)

DB_FILE = "smart_heat_engine.db"

MAX_RETRIES = 3
RETRY_DELAY = 2
FAILSAFE_DEFAULT_HIT = 75
ALERT_THRESHOLD = 75

# ==================================================
# DATABASE (AUTO MIGRATION)
# ==================================================
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def migrate_db():
    conn = get_db()
    cur = conn.cursor()

    # alerts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        hit INTEGER,
        state TEXT,
        severity TEXT,
        status TEXT,
        ack_by TEXT,
        ack_time TEXT,
        resolved_time TEXT
    )
    """)

    # live status table (single row)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_status (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        timestamp TEXT,
        cpu REAL,
        ram REAL,
        hit INTEGER,
        state TEXT,
        severity TEXT,
        failsafe INTEGER
    )
    """)

    conn.commit()
    conn.close()

# Run migration at startup
migrate_db()

# ==================================================
# DATA MODELS
# ==================================================
class AckInput(BaseModel):
    ack_by: str

# ==================================================
# CORE LOGIC
# ==================================================
def analyze_hit(hit: int):
    if hit < 60:
        return ("MONITOR", "GREEN", [])
    elif hit < 65:
        return ("WARNING", "YELLOW", ["notify_company"])
    elif hit < 70:
        return ("FAN_ON", "ORANGE", ["fan_on"])
    elif hit < 75:
        return ("FULL_COOLING", "RED", ["fan_on", "fan_speed_high", "cooling_system_on"])
    elif hit < 90:
        return ("DATA_SHIFT", "CRITICAL", [
            "fan_on",
            "fan_speed_high",
            "cooling_system_on",
            "data_shift_gradual"
        ])
    else:
        return ("EMERGENCY_SHUTDOWN", "BLACK", ["shutdown_server"])

# ==================================================
# REAL SENSOR WITH RETRY + FAIL-SAFE
# ==================================================
def read_real_sensor():
    for _ in range(MAX_RETRIES):
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            hit = max(cpu, ram)
            return cpu, ram, hit, 0
        except Exception:
            time.sleep(RETRY_DELAY)

    return None, None, FAILSAFE_DEFAULT_HIT, 1

# ==================================================
# DATABASE HELPERS
# ==================================================
def insert_alert(hit, state, severity):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO alerts (timestamp, hit, state, severity, status)
    VALUES (?, ?, ?, ?, 'OPEN')
    """, (datetime.utcnow().isoformat(), hit, state, severity))
    conn.commit()
    conn.close()

def update_live_status(cpu, ram, hit, state, severity, failsafe):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO live_status
    (id, timestamp, cpu, ram, hit, state, severity, failsafe)
    VALUES (1, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), cpu, ram, hit, state, severity, failsafe))
    conn.commit()
    conn.close()

# ==================================================
# ROUTES
# ==================================================
@app.get("/")
def root():
    return {"message": "Smart Heat Engine API running 🚀"}

@app.get("/api/live-status")
def live_status():
    cpu, ram, hit, failsafe = read_real_sensor()
    state, severity, actions = analyze_hit(hit)

    update_live_status(cpu, ram, hit, state, severity, failsafe)

    if hit >= ALERT_THRESHOLD:
        insert_alert(hit, state, severity)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": cpu,
        "ram": ram,
        "hit": hit,
        "state": state,
        "severity": severity,
        "recommended_actions": actions,
        "alert_active": hit >= ALERT_THRESHOLD,
        "failsafe": bool(failsafe),
        "display_target": "SERVER_TEAM_SCREEN"
    }

@app.get("/api/alerts")
def get_alerts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    alerts = []
    for r in rows:
        alerts.append({
            "id": r[0],
            "timestamp": r[1],
            "hit": r[2],
            "state": r[3],
            "severity": r[4],
            "status": r[5],
            "ack_by": r[6],
            "ack_time": r[7],
            "resolved_time": r[8]
        })

    return {"count": len(alerts), "alerts": alerts}

@app.post("/api/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, data: AckInput):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE alerts
    SET status='ACK', ack_by=?, ack_time=?
    WHERE id=? AND status='OPEN'
    """, (data.ack_by, datetime.utcnow().isoformat(), alert_id))
    conn.commit()
    conn.close()

    return {"message": "Alert acknowledged"}

@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE alerts
    SET status='RESOLVED', resolved_time=?
    WHERE id=? AND status!='RESOLVED'
    """, (datetime.utcnow().isoformat(), alert_id))
    conn.commit()
    conn.close()

    return {"message": "Alert resolved"}

@app.get("/api/live-snapshot")
def live_snapshot():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM live_status WHERE id=1")
    r = cur.fetchone()
    conn.close()

    if not r:
        return {"message": "No data yet"}

    return {
        "timestamp": r[1],
        "cpu": r[2],
        "ram": r[3],
        "hit": r[4],
        "state": r[5],
        "severity": r[6],
        "failsafe": bool(r[7])
    }