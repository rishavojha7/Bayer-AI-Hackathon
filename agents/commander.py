from core.logger import step


def commander_agent(state):
    metric = state.get("metrics_data", {})
    latency = metric.get("latency_ms", 0)

    # -----------------------------
    # Incident classification
    # -----------------------------
    if latency >= 1500:
        severity = "critical"
    elif latency >= 800:
        severity = "high"
    else:
        severity = "medium"

    incident_type = "latency_spike"

    service = state.get("alert", {}).get("service", "checkout")

    step("detect", f"Latency anomaly detected on service={service}")
    step("commander", f"Severity classified as {severity.upper()}")
    step("plan", "Dispatching Logs, Metrics, and Deploy agents")

    return {
        "alert": {
            "service": service,
            "severity": severity,
            "type": incident_type,
            "observed_latency_ms": latency
        }
    }
