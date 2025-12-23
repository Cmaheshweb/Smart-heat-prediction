import time
import random
import requests

API_URL = "https://smart-heat-prediction-13.onrender.com/api/analyze"

# -----------------------------
# LOAD PATTERN DEFINITIONS
# -----------------------------

def get_hit_by_phase(phase):
    if phase == "LOW":
        return random.randint(30, 50)
    elif phase == "MEDIUM":
        return random.randint(55, 70)
    elif phase == "HIGH":
        return random.randint(75, 95)

# -----------------------------
# MAIN SENSOR LOOP
# -----------------------------

def run_sensor():
    print("\nSMART HEAT SENSOR SIMULATION STARTED\n")

    phases = [
        ("LOW", 5),
        ("MEDIUM", 5),
        ("HIGH", 5),
    ]

    while True:
        for phase, cycles in phases:
            for _ in range(cycles):
                hit = get_hit_by_phase(phase)

                print(f"[{phase} LOAD] Generated HIT = {hit}")

                payload = {
                    "hit": hit
                }

                try:
                    response = requests.post(API_URL, json=payload, timeout=5)
                    data = response.json()

                    print("→ STATE   :", data.get("state"))
                    print("→ SEVERITY:", data.get("severity"))
                    print("→ ACTIONS :", data.get("actions"))

                except Exception as e:
                    print("❌ API ERROR:", e)

                print("-" * 50)
                time.sleep(5)  # ⏱️ Sensor interval (5 seconds)

# -----------------------------
# ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    run_sensor()