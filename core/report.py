# core/report.py
def report(state):
    action = state.get("action", {})
    action_type = action.get("type", "UNKNOWN")

    if action_type == "ROLLBACK":
        action_summary = "Autonomous rollback executed (DB_POOL_SIZE restored to 20)"
    elif action_type == "ESCALATE":
        action_summary = "Incident escalated to human SRE team for review"
    elif action_type == "NO_ACTION":
        action_summary = "No remediation executed; system continuing observation"
    else:
        action_summary = "No action information available"

    state["report"] = f"""
INCIDENT RCA REPORT

Service: checkout
Issue: Latency spike
Root Cause: {state.get('root_cause')}
Confidence: {state.get('confidence')}
Decision: {state.get('decision')}
Action Taken: {action_summary}
"""

    return state
