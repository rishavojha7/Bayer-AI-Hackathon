# core/logger.py
import time

def step(agent: str, message: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [{agent.upper()}] {message}")
