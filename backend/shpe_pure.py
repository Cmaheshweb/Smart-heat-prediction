import random, time, threading

class SHPEngine:
    def __init__(self, rows=600):
        self.rows = rows
        self.lock = threading.Lock()
        self.latest = {"step": 0, "cpu": None, "pred": None, "risk": None, "log": []}
        self._stop = False

    def collect_sample(self):
        cpu = 30 + random.random()*3
        for _ in range(self.rows):
            spike = 1 if (_ % 37 == 0) else 0
            cpu = max(5, cpu + (random.random()-0.5)*1.5 + spike*6)
            yield cpu

    def build_features(self, history, idx):
        cpu = history[idx]
        ma5 = sum(history[max(0,idx-4):idx+1]) / len(history[max(0,idx-4):idx+1])
        ma15 = sum(history[max(0,idx-14):idx+1]) / len(history[max(0,idx-14):idx+1])
        slope = (history[idx] - history[idx-5]) / 5 if idx >= 5 else 0
        return cpu, ma5, ma15, slope

    def predict(self, cpu, ma5, ma15, slope):
        return cpu*0.6 + ma5*0.2 + ma15*0.15 + slope*6

    def start(self, interval=0.3):
        def loop():
            history = []
            step = 0

            for cpu in self.collect_sample():
                history.append(cpu)
                cpu, ma5, ma15, slope = self.build_features(history, len(history)-1)
                pred = round(self.predict(cpu, ma5, ma15, slope), 2)
                risk = round(pred - cpu, 2)

                with self.lock:
                    self.latest.update(step=step, cpu=round(cpu,2), pred=pred, risk=risk)
                    self.latest["log"].append(f"Step {step}: CPU={cpu:.2f} Pred={pred} RiskDelta={risk}")
                    if len(self.latest["log"]) > 200: self.latest["log"].pop(0)

                step += 1
                time.sleep(interval)

        threading.Thread(target=loop, daemon=True).start()

    def get_status(self):
        with self.lock:
            return dict(self.latest)