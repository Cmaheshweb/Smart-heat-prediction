def evaluate_hit(hit):
    result = {
        "hit": hit,
        "state": "MONITOR",
        "actions": [],
        "severity": "GREEN"
    }

    if hit < 60:
        result["state"] = "MONITOR"
        result["severity"] = "GREEN"

    elif hit < 65:
        result["state"] = "WARNING"
        result["actions"] = ["notify_company"]
        result["severity"] = "YELLOW"

    elif hit < 70:
        result["state"] = "FAN_ON"
        result["actions"] = ["fan_on"]
        result["severity"] = "ORANGE"

    elif hit < 75:
        result["state"] = "FULL_COOLING"
        result["actions"] = ["fan_on", "fan_speed_high", "cooling_on"]
        result["severity"] = "RED"

    elif hit < 80:
        result["state"] = "GRADUAL_DATA_SHIFT"
        result["actions"] = [
            "fan_on",
            "fan_speed_high",
            "cooling_on",
            "data_shift_gradual"
        ]
        result["severity"] = "RED"

    elif hit < 89:
        result["state"] = "FAST_DATA_SHIFT"
        result["actions"] = [
            "fan_on",
            "fan_speed_high",
            "cooling_on",
            "data_shift_fast"
        ]
        result["severity"] = "CRITICAL"

    else:
        result["state"] = "EMERGENCY_SHUTDOWN"
        result["actions"] = ["shutdown_server"]
        result["severity"] = "BLACK"

    return result


# ----------- TESTING -----------
if __name__ == "__main__":
    test_hits = [45, 60, 65, 70, 76, 82, 90]

    for h in test_hits:
        print(evaluate_hit(h))