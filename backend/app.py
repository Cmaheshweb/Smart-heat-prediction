from flask import Flask, jsonify
from shpe_pure import SHPEngine
import os

app = Flask(__name__)

engine = SHPEngine(rows=600)
engine.start(interval=0.3)

@app.route("/api/status")
def status():
    s = engine.get_status()
    s["log"] = s.get("log", [])[-30:]
    return jsonify(s)

@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))