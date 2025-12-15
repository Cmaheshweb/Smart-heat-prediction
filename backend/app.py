from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/v1/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/v1/status")
def status():
    return jsonify({
        "service": "Smart Heat Prediction",
        "state": "running"
    })


@app.route("/api/v1/predict", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        data = request.get_json()
        temp = float(data.get("temperature", 0))
    else:
        temp = float(request.args.get("temperature", 0))

    if temp < 40:
        risk = "LOW"
        score = 0.2
        message = "System temperature normal"
        action = "No action required"
    elif temp < 75:
        risk = "MEDIUM"
        score = 0.6
        message = "Heat level rising"
        action = "Monitor system closely"
    else:
        risk = "HIGH"
        score = 0.9
        message = "Critical heat level detected"
        action = "Reduce load immediately"

    return jsonify({
        "temperature": temp,
        "risk": risk,
        "score": score,
        "message": message,
        "action": action
    })


if __name__ == "__main__":
    app.run(debug=True)