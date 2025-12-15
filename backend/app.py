@app.route("/api/v1/predict", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        data = request.get_json()
        temperature = float(data.get("temperature", 0))
    else:
        temperature = float(request.args.get("temperature", 0))

    if temperature < 40:
        return jsonify({
            "risk": "LOW",
            "score": 0.2,
            "message": "System temperature normal",
            "action": "No action required"
        })

    elif temperature < 75:
        return jsonify({
            "risk": "MEDIUM",
            "score": 0.6,
            "message": "Heat level rising",
            "action": "Monitor system closely"
        })

    else:
        return jsonify({
            "risk": "HIGH",
            "score": 0.9,
            "message": "Critical heat level detected",
            "action": "Reduce load immediately"
        })