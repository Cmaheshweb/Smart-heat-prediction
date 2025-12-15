from flask import Flask, jsonify, request, render_template_string
from shpe_pure import SHPEngine
from datetime import datetime
import os

app = Flask(__name__)

# ---------------- SHPE ENGINE ----------------
engine = SHPEngine(rows=600)
engine.start(interval=0.3)

# ---------------- SIMPLE UI ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Heat Prediction</title>
    <style>
        body {
            font-family: Arial;
            background: #0f172a;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .card {
            background: #111827;
            padding: 25px;
            border-radius: 12px;
            width: 320px;
            box-shadow: 0 0 20px rgba(0,0,0,0.6);
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            border-radius: 6px;
            border: none;
            font-size: 16px;
        }
        button {
            background: #22c55e;
            color: black;
            font-weight: bold;
            cursor: pointer;
        }
        .result {
            margin-top: 15px;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔥 Smart Heat Prediction</h2>
        <input id="temp" type="number" placeholder="Enter temperature">
        <button onclick="predict()">Predict</button>
        <div class="result" id="result"></div>
    </div>

<script>
function predict() {
    const t = document.getElementById("temp").value;

    fetch("/api/v1/predict", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ temperature: Number(t) })
    })
    .then(r => r.json())
    .then(d => {
        document.getElementById("result").innerHTML =
            "<b>Risk:</b> " + d.risk +
            "<br><b>Score:</b> " + d.score +
            "<br><b>Message:</b> " + d.message +
            "<br><b>Action:</b> " + d.recommended_action;
    })
    .catch(() => {
        document.getElementById("result").innerHTML = "Error!";
    });
}
</script>
</body>
</html>
"""

# ---------------- UI ROUTE ----------------
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

# ---------------- HEALTH CHECK ----------------
@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})

# ---------------- SYSTEM STATUS ----------------
@app.route("/api/status")
def status():
    s = engine.get_status()
    s["log"] = s.get("log", [])[-30:]
    return jsonify(s)

# ---------------- SMART PREDICTION API ----------------
@app.route("/api/v1/predict", methods=["POST"])
def predict():
    data = request.json or {}
    temperature = data.get("temperature")

    # Validation
    if temperature is None:
        return jsonify({"error": "temperature missing"}), 400

    if not isinstance(temperature, (int, float)):
        return jsonify({"error": "temperature must be number"}), 400

    if temperature < -50 or temperature > 200:
        return jsonify({"error": "temperature out of safe range"}), 400

    # Risk Logic
    if temperature >= 75:
        risk = "HIGH"
        score = round(min(1.0, temperature / 100), 2)
        message = "Critical heat level detected"
        action = "Reduce load immediately"

    elif temperature >= 45:
        risk = "MEDIUM"
        score = round(temperature / 100, 2)
        message = "Heat level rising"
        action = "Monitor system closely"

    else:
        risk = "LOW"
        score = round(temperature / 100, 2)
        message = "System temperature normal"
        action = "No action required"

    return jsonify({
        "temperature": temperature,
        "risk": risk,
        "score": score,
        "message": message,
        "recommended_action": action,
        "timestamp": datetime.utcnow().isoformat()
    })

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )