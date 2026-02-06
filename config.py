"""
Configuration for Metrics Agent
Defines thresholds and detection parameters
"""

# Metric thresholds and detection parameters
THRESHOLDS = {
    "cpu_usage_percent": {
        "threshold": 80,
        "description": "CPU usage exceeding 80% may indicate resource constraints"
    },
    "memory_usage_percent": {
        "threshold": 85,
        "description": "Memory usage exceeding 85% may lead to OOM issues"
    },
    "p99_latency_ms": {
        "threshold": 1500,
        "description": "P99 latency exceeding 1500ms indicates performance degradation"
    },
    "avg_latency_ms": {
        "threshold": 800,
        "description": "Average latency exceeding 800ms impacts user experience"
    },
    "memory_leak_rate_mb_per_min": {
        "threshold": 5.0,
        "description": "Memory leak rate exceeding 5 MB/min indicates a memory leak"
    },
    "error_rate_percent": {
        "threshold": 2.0,
        "description": "Error rate exceeding 2% indicates system instability"
    },
    "request_rate_rps": {
        "threshold": 1000,
        "description": "Request rate for monitoring capacity (not necessarily an anomaly threshold)",
        "direction": "monitor"  # Can be high or low
    }
}

# Sliding window configuration
SLIDING_WINDOW_SIZE = 5

# Confidence scoring weights
CONFIDENCE_WEIGHTS = {
    "consecutive_breaches": 20,  # Points per consecutive breach
    "threshold_excess": 15,      # Points per 10% over threshold
    "window_saturation": 10,     # Points if most of window shows anomaly
}
