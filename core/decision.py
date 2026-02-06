# core/decision.py
from core.logger import step

def decide(state):
    step("decide", f"Root cause confidence={state['confidence']}")

    if state["confidence"] > 0.8:
        state["decision"] = "ROLLBACK"
        step("decide", "Rollback approved")
    else:
        state["decision"] = "ESCALATE"
        step("decide", "Escalating to human SRE")

    return state
