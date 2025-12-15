from flask import Flask, jsonify, request, send_from_directory
from shpe_pure import SHPEngine
import os

app = Flask(__name__)

# ---- SHP Engine ----
engine = SHPEngine(rows=600)
engine.start(interval=0.3)

# ---- Home UI ----
@app.route("/")
def home():
    return send_from_directory("backend", "index.html")

# ---- Health check ----
@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})

# ---- System status ----
@app.route("/api/status")
def status():
    s = engine.get_status()
    s["log"] = s.get("log", [])[-30:]
    return jsonify(s)

# ---- Heat prediction ----
@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json or {}

    temperature = data.get("temperature")
    if temperature is None:
        return jsonify({"error": "temperature missing"}), 400

    if temperature > 70:
        risk = "HIGH"
    elif temperature > 50:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return jsonify({
        "temperature": temperature,
        "risk": risk
    })

# ---- Run server ----
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )