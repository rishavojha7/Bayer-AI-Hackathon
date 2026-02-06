import time
import json
import random
import uuid
import os
from datetime import datetime

# =====================================================
# Configuration
# =====================================================
TOTAL_EVENTS = 10
SLEEP_SECONDS = 1

NORMAL_DIR = "normal"
ANOMALY_DIR = "anomalies"

os.makedirs(NORMAL_DIR, exist_ok=True)
os.makedirs(ANOMALY_DIR, exist_ok=True)

# Randomly select which event will be anomalous
ANOMALY_INDEX = random.randint(0, TOTAL_EVENTS - 1)


# =====================================================
# Utility
# =====================================================
def iso_timestamp():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# =====================================================
# Telemetry Generator
# =====================================================
def generate_telemetry(is_anomalous: bool) -> dict:
    if is_anomalous:
        metrics = {
            "cpu_usage_percent": random.randint(82, 95),
            "memory_usage_percent": random.randint(85, 97),
            "p99_latency_ms": random.randint(1800, 2600),
            "avg_latency_ms": random.randint(700, 1200),
            "memory_leak_rate_mb_per_min": round(random.uniform(5.0, 12.0), 2),
            "error_rate_percent": round(random.uniform(4.0, 8.0), 2),
            "request_rate_rps": random.randint(900, 1400)
        }
    else:
        metrics = {
            "cpu_usage_percent": random.randint(35, 60),
            "memory_usage_percent": random.randint(55, 70),
            "p99_latency_ms": random.randint(250, 420),
            "avg_latency_ms": random.randint(120, 260),
            "memory_leak_rate_mb_per_min": round(random.uniform(0.1, 0.6), 2),
            "error_rate_percent": round(random.uniform(0.1, 0.5), 2),
            "request_rate_rps": random.randint(400, 800)
        }

    return {
        "event_id": f"EVT-{uuid.uuid4()}",
        "timestamp": iso_timestamp(),
        "service": "checkout-service",
        "environment": "production",
        "metrics": metrics
    }


# =====================================================
# Monitoring / Verification Layer (Rule-Based)
# =====================================================
def evaluate_severity(metrics: dict) -> str:
    if (
        metrics["p99_latency_ms"] > 1500 or
        metrics["cpu_usage_percent"] > 85 or
        metrics["memory_usage_percent"] > 90 or
        metrics["memory_leak_rate_mb_per_min"] > 4 or
        metrics["error_rate_percent"] > 3
    ):
        return "SEVERE"

    if (
        metrics["p99_latency_ms"] > 800 or
        metrics["cpu_usage_percent"] > 70
    ):
        return "WARNING"

    return "NORMAL"


# =====================================================
# Main Execution
# =====================================================
print("\n🚀 Starting Telemetry Generation (10 events)\n")

for i in range(TOTAL_EVENTS):
    is_anomaly = (i == ANOMALY_INDEX)

    telemetry = generate_telemetry(is_anomaly)
    severity = evaluate_severity(telemetry["metrics"])
    telemetry["severity"] = severity

    # Terminal output
    if severity == "SEVERE":
        print("SEVERE ANOMALY DETECTED 🚨")
    elif severity == "WARNING":
        print("WARNING")
    else:
        print("NORMAL")

    print(json.dumps(telemetry, indent=2))
    print("-" * 90)

    # Persist based on severity
    if severity == "SEVERE":
        path = os.path.join(
            ANOMALY_DIR, f"anomaly_{telemetry['event_id']}.json"
        )
        with open(path, "w") as f:
            json.dump(telemetry, f, indent=2)

    elif severity == "NORMAL":
        path = os.path.join(
            NORMAL_DIR, f"normal_{telemetry['event_id']}.json"
        )
        with open(path, "w") as f:
            json.dump(telemetry, f, indent=2)

    time.sleep(SLEEP_SECONDS)

print("\nDone. NORMAL and SEVERE data persisted to respective folders.\n")
