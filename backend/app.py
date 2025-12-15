from flask import Flask, jsonify
from shpe_pure import SHPEngine
import os
from flask import Flask, jsonify, request
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
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/ping")
def ping():
    return jsonify(ok=True)

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json

    temperature = data.get("temperature")

    if temperature is None:
        return jsonify(error="temperature missing"), 400

    if temperature > 70:
        risk = "HIGH"
    elif temperature > 50:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return jsonify(
        temperature=temperature,
        risk=risk
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
