# core/action.py
from core.logger import step


def act(state):
    decision = state.get("decision")

    # -----------------------------
    # Autonomous remediation
    # -----------------------------
    if decision == "ROLLBACK":
        step("act", "Executing autonomous rollback on checkout service")
        step("act", "Restoring DB_POOL_SIZE=20")

        state["action"] = {
            "type": "ROLLBACK",
            "service": "checkout",
            "restore_config": {"DB_POOL_SIZE": 20},
            "autonomy": "FULL"
        }

    # -----------------------------
    # Human handover
    # -----------------------------
    elif decision == "ESCALATE":
        step("act", "Confidence insufficient for autonomous action")
        step("act", "Escalating incident to human SRE team")

        state["action"] = {
            "type": "ESCALATE",
            "service": "checkout",
            "reason": "Low confidence in root cause",
            "recommended_next_steps": [
                "Review DB metrics",
                "Inspect recent deployments",
                "Validate rollback safety"
            ],
            "autonomy": "HUMAN_IN_LOOP"
        }

    # -----------------------------
    # Safe no-op
    # -----------------------------
    else:
        step("act", "No remediation action taken")
        step("act", "Continuing observation")

        state["action"] = {
            "type": "NO_ACTION",
            "service": "checkout",
            "autonomy": "OBSERVE_ONLY"
        }

    return state
