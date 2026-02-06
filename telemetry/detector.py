from collections import deque
from core.logger import step

WINDOW = deque(maxlen=3)
THRESHOLD = 700


def detect_incident(metric):
    latency = metric.get("latency_ms", 0)
    WINDOW.append(latency)

    if len(WINDOW) == 3 and all(l >= THRESHOLD for l in WINDOW):
        step("detect", f"Sustained latency breach: {list(WINDOW)}")
        return True

    return False


def reset_detector():
    """
    Clear detector memory after incident resolution
    to avoid residual anomaly bias.
    """
    WINDOW.clear()
