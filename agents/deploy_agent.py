from core.logger import step

def deploy_agent(state):
    change = state["deploy_data"]["config_change"]

    step("deploy", "Analyzing CI/CD timeline")
    step("deploy", f"Detected recent config change: {change}")

    return {
        "deploy_findings": {
            "recent_deploy": True,
            "change": change
        }
    }
