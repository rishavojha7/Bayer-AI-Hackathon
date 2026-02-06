import psutil
import time
from datetime import datetime
import json
import os

# Configuration
LOG_FILE = "metrics.log"
INTERVAL_SECONDS = 5  # Log every 5 seconds

def get_cpu_metrics():
    """Collect CPU and system resource metrics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "memory_percent": psutil.virtual_memory().percent,
        "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
        "memory_total_mb": psutil.virtual_memory().total / (1024 * 1024),
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "load_average_1min": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
    }

def append_to_log(metrics, log_file):
    """Append metrics to log file in JSON format"""
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(metrics, f)
            f.write('\n')
        return True
    except Exception as e:
        print(f"Error writing to log file: {e}")
        return False

def main():
    """Main monitoring loop"""
    print(f"🔍 CPU Resource Monitor Started")
    print(f"📊 Logging to: {os.path.abspath(LOG_FILE)}")
    print(f"⏱️  Interval: {INTERVAL_SECONDS} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    try:
        iteration = 0
        while True:
            # Collect metrics
            metrics = get_cpu_metrics()
            
            # Append to log file
            if append_to_log(metrics, LOG_FILE):
                iteration += 1
                print(f"[{iteration}] {metrics['timestamp']} | "
                      f"CPU: {metrics['cpu_percent']:.1f}% | "
                      f"Memory: {metrics['memory_percent']:.1f}% | "
                      f"Disk: {metrics['disk_usage_percent']:.1f}%")
            
            # Wait for next interval
            time.sleep(INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")
        print(f"📁 Metrics saved to: {os.path.abspath(LOG_FILE)}")

if __name__ == "__main__":
    main()
