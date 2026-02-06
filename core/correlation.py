from core.logger import step


def correlate(state):
    step("correlate", "Cross-referencing logs, metrics, and deploy data")

    confidence = 0.0
    hypotheses = []

    # -----------------------------
    # Evidence 1: Logs
    # -----------------------------
    logs_error = state["logs_findings"].get("error")
    logs_count = state["logs_findings"].get("count", 0)

    if logs_error == "DBConnectionTimeout" and logs_count >= 3:
        confidence += 0.4
        hypotheses.append("Database connection exhaustion observed")
        step("correlate", "Log evidence supports DB instability")

    # -----------------------------
    # Evidence 2: Metrics
    # -----------------------------
    latency = state["metrics_findings"].get("latency_ms", 0)

    if latency >= 1000:
        confidence += 0.3
        hypotheses.append("Severe user-facing latency detected")
        step("correlate", "Metrics indicate high-impact latency")

    # -----------------------------
    # Evidence 3: Deploy Intelligence
    # -----------------------------
    recent_deploy = state["deploy_findings"].get("recent_deploy", False)
    change = state["deploy_findings"].get("change", {})

    if recent_deploy and "DB_POOL_SIZE" in change:
        confidence += 0.3
        hypotheses.append("Recent DB pool configuration change detected")
        step("correlate", "Deploy change aligns with observed failures")

    # -----------------------------
    # Root Cause Selection
    # -----------------------------
    if (
        "Database connection exhaustion observed" in hypotheses
        and "Recent DB pool configuration change detected" in hypotheses
    ):
        root_cause = "DB pool misconfiguration"
    elif "Database connection exhaustion observed" in hypotheses:
        root_cause = "Database overload or instability"
    elif latency >= 1000:
        root_cause = "Service performance degradation"
    else:
        root_cause = "Unknown — insufficient evidence"

    confidence = round(min(confidence, 1.0), 2)

    step(
        "correlate",
        f"Root cause hypothesis='{root_cause}', confidence={confidence}"
    )

    state["root_cause"] = root_cause
    state["confidence"] = confidence

    return state
