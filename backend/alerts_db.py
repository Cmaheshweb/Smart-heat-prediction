import sqlite3
from datetime import datetime

DB_NAME = "alerts.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (time, hit, state, severity) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), hit, state, severity)
    )
    conn.commit()
    conn.close()

def fetch_alerts(limit=100):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT time, hit, state, severity FROM alerts ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {"time": r[0], "hit": r[1], "state": r[2], "severity": r[3]}
        for r in rows
    ]