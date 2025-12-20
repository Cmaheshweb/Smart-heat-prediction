# smart_heat_engine.py
# Smart Heat Prediction & Action Engine
# Final logic as discussed (60% to 90%)

def smart_heat_engine(hit):
    result = {
        "hit": hit,
        "state": "",
        "severity": "",
        "actions": []
    }

    if hit < 60:
        result["state"] = "MONITOR"
        result["severity"] = "GREEN"

    elif hit < 65:
        result["state"] = "WARNING"
        result["severity"] = "YELLOW"
        result["actions"].append("notify_company")

    elif hit < 70:
        result["state"] = "FAN_ON"
        result["severity"] = "ORANGE"
        result["actions"].append("fan_on")

    elif hit < 75:
        result["state"] = "FULL_COOLING"
        result["severity"] = "RED"
        result["actions"].extend([
            "fan_on",
            "fan_speed_high",
            "cooling_system_on"
        ])

    elif hit < 80:
        result["state"] = "GRADUAL_DATA_SHIFT"
        result["severity"] = "RED"
        result["actions"].extend([
            "fan_on",
            "fan_speed_high",
            "cooling_system_on",
            "data_shift_gradual"
        ])

    elif hit < 90:
        result["state"] = "FAST_DATA_SHIFT"
        result["severity"] = "CRITICAL"
        result["actions"].extend([
            "fan_on",
            "fan_speed_high",
            "cooling_system_on",
            "data_shift_fast"
        ])

    else:
        result["state"] = "EMERGENCY_SHUTDOWN"
        result["severity"] = "BLACK"
        result["actions"].append("shutdown_server")

    return result


# ------------------ TESTING BLOCK ------------------

if __name__ == "__main__":
    print("SMART HEAT ENGINE TEST STARTED\n")

    test_hits = [45, 60, 65, 70, 76, 82, 90]

    for hit in test_hits:
        output = smart_heat_engine(hit)
        print(output)

    print("\nSMART HEAT ENGINE TEST COMPLETED")