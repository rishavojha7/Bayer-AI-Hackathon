from core.logger import step

def metrics_agent(state):
    latency = state["metrics_data"]["latency_ms"]

    step("metrics", f"p95 latency observed = {latency}ms")

    impact = "high" if latency >= 700 else "low"
    step("metrics", f"Impact classified as {impact}")

    return {
        "metrics_findings": {
            "latency_ms": latency,
            "impact": impact
        }
    }
