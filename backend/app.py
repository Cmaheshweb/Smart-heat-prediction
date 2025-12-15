from flask import Flask, jsonify, request, render_template_string
from shpe_pure import SHPEngine
import os

app = Flask(__name__)

# ---- SHP Engine ----
engine = SHPEngine(rows=600)
engine.start(interval=0.3)

# ---- SIMPLE UI ----
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
            width: 300px;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
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
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔥 Heat Prediction</h2>
        <input id="temp" type="number" placeholder="Enter temperature">
        <button onclick="predict()">Predict</button>
        <div class="result" id="result"></div>
    </div>

<script>
function predict() {
    const t = document.getElementById("temp").value;
    fetch("/api/predict", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({temperature: Number(t)})
    })
    .then(r => r.json())
    .then(d => {
        document.getElementById("result").innerHTML =
            "Risk Level: <b>" + d.risk + "</b>";
    })
    .catch(() => {
        document.getElementById("result").innerHTML = "Error!";
    });
}
</script>
</body>
</html>
"""

# ---- UI Route ----
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

# ---- Health Check ----
@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})

# ---- System Status ----
@app.route("/api/status")
def status():
    s = engine.get_status()
    s["log"] = s.get("log", [])[-30:]
    return jsonify(s)

# ---- Prediction ----
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

# ---- Run ----
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )