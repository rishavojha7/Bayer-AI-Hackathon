import time

from telemetry.log_stream import log_stream
from telemetry.metrics_stream import metrics_stream
from telemetry.deploy_stream import deploy_stream
from telemetry.detector import detect_incident, reset_detector

from graph import app


# ============================
# Incident lifecycle controls
# ============================
INCIDENT_COOLDOWN = 5   # seconds (demo-friendly)
last_incident_time = 0
incident_active = False


# ============================
# Live buffers
# ============================
logs_buffer = []
deploy_data = deploy_stream()

log_gen = log_stream()
metric_gen = metrics_stream()


print("Autonomous Incident Commander started...")
print("Monitoring telemetry streams...\n")


# ============================
# Main event loop
# ============================
while True:
    try:
        log = next(log_gen)
        metric = next(metric_gen)

        logs_buffer.append(log)

        print(f"[LOG STREAM] {log}")
        print(f"[METRIC STREAM] {metric}")

        now = time.time()

        # ============================
        # DETECT PHASE (cheap & continuous)
        # ============================
        if (
            detect_incident(metric)
            and not incident_active
            and (now - last_incident_time) > INCIDENT_COOLDOWN
        ):

            print("""
==========================
 AUTONOMOUS INCIDENT FLOW
 DETECT → PLAN → INVESTIGATE
 DECIDE → ACT → REPORT
==========================
""")

            print("INCIDENT DETECTED — Triggering agents...\n")

            incident_active = True
            last_incident_time = now

            # ============================
            # Build incident state
            # ============================
            state = {
                "alert": {},
                "logs_data": logs_buffer,
                "metrics_data": metric,
                "deploy_data": deploy_data,

                "logs_findings": None,
                "metrics_findings": None,
                "deploy_findings": None,

                "root_cause": None,
                "confidence": None,
                "decision": None,
                "action": None,
                "report": None
            }

            # ============================
            # Run agentic workflow
            # ============================
            result = app.invoke(state)

            print("\nINCIDENT RESOLVED\n")
            print(result["report"])

            # ============================
            # RESET for next incident
            # ============================
            incident_active = False
            logs_buffer.clear()
            reset_detector()

        time.sleep(1)

    except StopIteration:
        print("\nTelemetry stream ended. System still alive.")
        time.sleep(5)
