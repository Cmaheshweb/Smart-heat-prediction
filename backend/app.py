from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# --------------------
# ROOT (Health + UI)
# --------------------
@app.route("/")
def home():
    return "Smart Heat Prediction API is running 🚀", 200


# --------------------
# HEALTH CHECK
# --------------------
@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok"})


# --------------------
# SYSTEM STATUS
# --------------------
@app.route("/api/status")
def status():
    return jsonify({
        "service": "smart-heat-prediction",
        "state": "running"
    })


# --------------------
# SMART PREDICTION API
# --------------------
@app.route("/api/v1/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)

    if not data or "temperature" not in data:
        return jsonify({"error": "temperature missing"}), 400

    temp = float(data["temperature"])

    if temp >= 80:
        risk = "HIGH"
        score = 0.9
        message = "Critical heat level detected"
        action = "Reduce load immediately"
    elif temp >= 50:
        risk = "MEDIUM"
        score = 0.6
        message = "Heat level rising"
        action = "Monitor system closely"
    else:
        risk = "LOW"
        score = 0.2
        message = "System temperature normal"
        action = "No action required"

    return jsonify({
        "temperature": temp,
        "risk": risk,
        "score": score,
        "message": message,
        "action": action
    })


# --------------------
# RUN (Render compatible)
# --------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )