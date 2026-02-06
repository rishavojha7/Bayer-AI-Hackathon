from core.logger import step

def logs_agent(state):
    logs = state["logs_data"]
    step("logs", f"Scanning {len(logs)} log lines")

    errors = [l for l in logs if "DBConnectionTimeout" in l]

    step("logs", f"Detected DBConnectionTimeout x{len(errors)}")

    return {
        "logs_findings": {
            "error": "DBConnectionTimeout",
            "count": len(errors)
        }
    }
