# telemetry/metrics_stream.py
import random

def metrics_stream():
    while True:
        yield {
            "latency_ms": random.choice([120, 200, 350, 800, 1200, 1800, 2000, 2200])
        }
