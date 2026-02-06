# telemetry/log_stream.py
import random

ERRORS = [
    "ERROR DBConnectionTimeout",
    "ERROR Connection pool exhausted",
    "WARN Retry attempt"
]

def log_stream():
    while True:
        yield random.choice(ERRORS + ["INFO Request completed"])
