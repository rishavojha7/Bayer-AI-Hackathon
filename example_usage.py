"""
Example usage of the Metrics Agent

Demonstrates the refactored agent with Analyzer and Trend tools
Uses the sample metrics from metrics_agent2.txt
"""

from metrics_agent import process_metric, reset_trend_analyzer
import json
import time


def main():
    # Simulate steadily increasing memory usage
    for i in range(1):
        leak_metrics = {
            "cpu_usage_percent": 60 + i * 2,
            "memory_usage_percent": 65 + i * 5,
            "p99_latency_ms": 700 + i * 100,
            "avg_latency_ms": 400 + i * 50,
            "memory_leak_rate_mb_per_min": 2.0 + i * 2.0,
            "error_rate_percent": 0.8 + i * 0.3,
            "request_rate_rps": 900
        }
        print(f"Processing data point {i+1}... (Memory: {leak_metrics['memory_usage_percent']}%, Leak rate: {leak_metrics['memory_leak_rate_mb_per_min']:.1f} MB/min)")
        result = process_metric(leak_metrics)
        print(json.dumps(result, indent=2))
        time.sleep(0.5)


if __name__ == "__main__":
    main()
