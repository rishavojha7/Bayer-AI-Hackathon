import psutil
import time
import threading
from datetime import datetime
import json
import os

# Configuration
LOG_FILE = "metrics.log"
INTERVAL_SECONDS = 5  # Log every 5 seconds

class CPUMonitorThread(threading.Thread):
    """CPU Monitor running as a daemon thread"""
    
    def __init__(self, log_file=LOG_FILE, interval=INTERVAL_SECONDS):
        super().__init__()
        self.log_file = log_file
        self.interval = interval
        self.daemon = True  # Thread will exit when main program exits
        self.running = True
        self.iteration = 0
        
    def get_cpu_metrics(self):
        """Collect CPU and system resource metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_mb": round(psutil.virtual_memory().available / (1024 * 1024), 2),
            "memory_total_mb": round(psutil.virtual_memory().total / (1024 * 1024), 2),
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "load_average_1min": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
        }
    
    def append_to_log(self, metrics):
        """Append metrics to log file in JSON format"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(metrics, f)
                f.write('\n')
            return True
        except Exception as e:
            print(f"Error writing to log file: {e}")
            return False
    
    def run(self):
        """Main monitoring loop running in thread"""
        print(f"🔍 CPU Monitor Thread Started (Background)")
        print(f"📊 Logging to: {os.path.abspath(self.log_file)}")
        print(f"⏱️  Interval: {self.interval} seconds\n")
        
        while self.running:
            try:
                # Collect metrics
                metrics = self.get_cpu_metrics()
                
                # Append to log file
                if self.append_to_log(metrics):
                    self.iteration += 1
                    print(f"[Monitor-{self.iteration}] {metrics['timestamp']} | "
                          f"CPU: {metrics['cpu_percent']:.1f}% | "
                          f"Memory: {metrics['memory_percent']:.1f}% | "
                          f"Disk: {metrics['disk_usage_percent']:.1f}%")
                
                # Wait for next interval
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"Error in monitoring thread: {e}")
                time.sleep(self.interval)
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        print("\n✓ Monitor thread stopped")


def main():
    """Demo: Run monitor as background thread while doing other work"""
    
    # Start CPU monitor thread
    monitor = CPUMonitorThread(log_file="metrics.log", interval=5)
    monitor.start()
    
    print("="*60)
    print("Main program running with background CPU monitoring...")
    print("The monitor logs to metrics.log in the background")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    try:
        # Simulate main program work
        counter = 0
        while True:
            counter += 1
            print(f"[Main-{counter}] Main program doing work...")
            time.sleep(10)  # Main program sleeps while monitor continues
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        monitor.stop()
        time.sleep(1)
        print(f"📁 Metrics saved to: {os.path.abspath(monitor.log_file)}")


if __name__ == "__main__":
    main()
