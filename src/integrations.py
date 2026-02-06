#!/usr/bin/env python3
"""
Integration Examples for Autonomous First Responder
Demonstrates integration with real-world monitoring and observability platforms

Supported Integrations:
- Prometheus/Grafana for metrics
- ELK Stack for logs
- PagerDuty for alerting
- Kubernetes for orchestration
- AWS CloudWatch
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


# =============================================================================
# PROMETHEUS METRICS INTEGRATION
# =============================================================================

@dataclass
class PrometheusQuery:
    """Prometheus query configuration"""
    query: str
    service: str
    metric_type: str


class PrometheusMetricsAdapter:
    """Adapter for Prometheus metrics backend"""
    
    def __init__(self, prometheus_url: str = "http://prometheus:9090"):
        self.prometheus_url = prometheus_url
        self.common_queries = {
            "cpu_usage": 'rate(process_cpu_seconds_total{{service="{service}"}}[5m]) * 100',
            "memory_usage": 'process_resident_memory_bytes{{service="{service}"}} / 1024 / 1024',
            "error_rate": 'rate(http_requests_total{{service="{service}",status=~"5.."}}[5m])',
            "p99_latency": 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m]))',
            "request_rate": 'rate(http_requests_total{{service="{service}"}}[5m])'
        }
    
    async def query_metrics(self, service: str) -> Dict[str, float]:
        """Query current metrics for a service"""
        # In real implementation, use prometheus_client or requests
        # Here we simulate the query
        
        print(f"[PrometheusAdapter] Querying metrics for {service}...")
        await asyncio.sleep(0.2)
        
        # Simulate metrics retrieval
        metrics = {
            "cpu_usage": 78.5,
            "memory_usage_mb": 1840.2,
            "error_rate": 0.15,
            "p99_latency_ms": 2340,
            "request_rate": 450.2,
            "active_connections": 234
        }
        
        return metrics
    
    async def get_historical_metrics(self, service: str, 
                                    duration_minutes: int = 30) -> List[Dict[str, Any]]:
        """Get historical metrics for trend analysis"""
        print(f"[PrometheusAdapter] Fetching {duration_minutes}min history for {service}...")
        await asyncio.sleep(0.3)
        
        # Simulate time series data
        history = []
        now = datetime.now()
        
        for i in range(duration_minutes):
            timestamp = now - timedelta(minutes=duration_minutes - i)
            history.append({
                "timestamp": timestamp.isoformat(),
                "cpu_usage": 45 + (i * 1.2) if i < 20 else 78,  # Spike at 20min
                "error_rate": 0.01 + (i * 0.007) if i < 20 else 0.15,
                "p99_latency_ms": 250 + (i * 100) if i < 20 else 2340
            })
        
        return history


# =============================================================================
# ELASTICSEARCH LOGS INTEGRATION
# =============================================================================

class ElasticsearchLogsAdapter:
    """Adapter for Elasticsearch/ELK stack"""
    
    def __init__(self, es_url: str = "http://elasticsearch:9200"):
        self.es_url = es_url
        self.index_pattern = "logs-*"
    
    async def search_logs(self, service: str, 
                         time_range_minutes: int = 15,
                         severity: str = "error") -> List[Dict[str, Any]]:
        """Search logs for errors and stack traces"""
        print(f"[ElasticsearchAdapter] Searching logs: service={service}, severity={severity}")
        await asyncio.sleep(0.4)
        
        # Simulate Elasticsearch query
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"service": service}},
                        {"match": {"severity": severity}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range_minutes}m"}}}
                    ]
                }
            },
            "sort": [{"@timestamp": "desc"}],
            "size": 100
        }
        
        # Simulate results
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "service": service,
                "severity": "ERROR",
                "message": "Connection timeout to database",
                "stack_trace": "SQLException: Connection timeout\n  at db.pool.acquire()",
                "request_id": "req-abc123"
            },
            {
                "timestamp": (datetime.now() - timedelta(seconds=30)).isoformat(),
                "service": service,
                "severity": "ERROR",
                "message": "Failed to execute query",
                "stack_trace": "SQLException: Query execution failed",
                "request_id": "req-def456"
            }
        ]
        
        return logs
    
    async def aggregate_errors(self, service: str, 
                              time_range_minutes: int = 15) -> Dict[str, Any]:
        """Aggregate error patterns"""
        print(f"[ElasticsearchAdapter] Aggregating error patterns for {service}")
        await asyncio.sleep(0.3)
        
        aggregation = {
            "total_errors": 247,
            "unique_error_types": 5,
            "error_distribution": {
                "SQLException": 189,
                "TimeoutException": 34,
                "NullPointerException": 18,
                "IOException": 6
            },
            "affected_endpoints": ["/api/users", "/api/orders", "/api/payments"],
            "peak_error_time": (datetime.now() - timedelta(minutes=5)).isoformat()
        }
        
        return aggregation


# =============================================================================
# KUBERNETES INTEGRATION
# =============================================================================

class KubernetesAdapter:
    """Adapter for Kubernetes orchestration"""
    
    def __init__(self, namespace: str = "production"):
        self.namespace = namespace
    
    async def get_pod_status(self, service: str) -> Dict[str, Any]:
        """Get pod status and health"""
        print(f"[K8sAdapter] Getting pod status for {service}")
        await asyncio.sleep(0.2)
        
        # Simulate kubectl output
        status = {
            "deployment": service,
            "namespace": self.namespace,
            "replicas": {
                "desired": 5,
                "current": 5,
                "ready": 3,
                "unavailable": 2
            },
            "pods": [
                {"name": f"{service}-abc123", "status": "Running", "restarts": 0, "ready": True},
                {"name": f"{service}-def456", "status": "Running", "restarts": 0, "ready": True},
                {"name": f"{service}-ghi789", "status": "Running", "restarts": 0, "ready": True},
                {"name": f"{service}-jkl012", "status": "CrashLoopBackOff", "restarts": 5, "ready": False},
                {"name": f"{service}-mno345", "status": "Error", "restarts": 3, "ready": False}
            ],
            "events": [
                "Warning: Back-off restarting failed container",
                "Warning: Pod unhealthy"
            ]
        }
        
        return status
    
    async def scale_deployment(self, service: str, replicas: int) -> bool:
        """Scale deployment"""
        print(f"[K8sAdapter] Scaling {service} to {replicas} replicas")
        await asyncio.sleep(1.0)
        
        # Simulate kubectl scale command
        print(f"  ✅ Scaled deployment/{service} to {replicas}")
        return True
    
    async def rollback_deployment(self, service: str, revision: Optional[int] = None) -> bool:
        """Rollback deployment to previous version"""
        print(f"[K8sAdapter] Rolling back {service}" + 
              (f" to revision {revision}" if revision else " to previous"))
        await asyncio.sleep(1.5)
        
        print(f"  ✅ Rollback completed")
        return True
    
    async def restart_pods(self, service: str, strategy: str = "rolling") -> bool:
        """Restart pods with specified strategy"""
        print(f"[K8sAdapter] Restarting {service} pods ({strategy} restart)")
        await asyncio.sleep(2.0)
        
        print(f"  ✅ Rolling restart completed")
        return True


# =============================================================================
# PAGERDUTY INTEGRATION
# =============================================================================

class PagerDutyAdapter:
    """Adapter for PagerDuty incident management"""
    
    def __init__(self, api_key: str = "demo_key"):
        self.api_key = api_key
        self.service_id = "PXXXXXX"
    
    async def create_incident(self, alert: Any, severity: str = "critical") -> str:
        """Create PagerDuty incident"""
        print(f"[PagerDutyAdapter] Creating {severity} incident")
        await asyncio.sleep(0.3)
        
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        incident = {
            "id": incident_id,
            "type": "incident",
            "summary": alert.message,
            "severity": severity,
            "status": "triggered",
            "service": {"id": self.service_id, "type": "service"},
            "escalation_policy": {"id": "PXXXXXX", "type": "escalation_policy"}
        }
        
        print(f"  ✅ Created incident: {incident_id}")
        return incident_id
    
    async def update_incident(self, incident_id: str, 
                             status: str = "resolved",
                             note: str = "") -> bool:
        """Update incident status"""
        print(f"[PagerDutyAdapter] Updating incident {incident_id} -> {status}")
        if note:
            print(f"  Note: {note}")
        await asyncio.sleep(0.2)
        
        print(f"  ✅ Incident updated")
        return True


# =============================================================================
# INTEGRATED FIRST RESPONDER
# =============================================================================

class IntegratedFirstResponder:
    """First responder with real-world integrations"""
    
    def __init__(self):
        self.prometheus = PrometheusMetricsAdapter()
        self.elasticsearch = ElasticsearchLogsAdapter()
        self.kubernetes = KubernetesAdapter()
        self.pagerduty = PagerDutyAdapter()
    
    async def investigate_with_real_data(self, alert: Any) -> Dict[str, Any]:
        """Investigate using real monitoring data"""
        
        print(f"\n{'='*80}")
        print(f"INTEGRATED INVESTIGATION: {alert.id}")
        print(f"{'='*80}\n")
        
        service = alert.service
        
        # Parallel data collection from all sources
        print("📊 Collecting data from monitoring systems...\n")
        
        metrics, logs, k8s_status, log_aggregation = await asyncio.gather(
            self.prometheus.query_metrics(service),
            self.elasticsearch.search_logs(service),
            self.kubernetes.get_pod_status(service),
            self.elasticsearch.aggregate_errors(service)
        )
        
        # Get historical context
        historical_metrics = await self.prometheus.get_historical_metrics(service)
        
        # Analysis
        findings = {
            "metrics": metrics,
            "logs": {
                "recent_errors": logs[:5],
                "aggregation": log_aggregation
            },
            "kubernetes": k8s_status,
            "historical_trends": historical_metrics[-5:]  # Last 5 data points
        }
        
        print("\n🔍 DATA COLLECTION COMPLETE\n")
        print(f"Metrics: CPU={metrics['cpu_usage']:.1f}%, Errors={metrics['error_rate']:.2%}")
        print(f"Logs: {log_aggregation['total_errors']} errors found")
        print(f"K8s: {k8s_status['replicas']['ready']}/{k8s_status['replicas']['desired']} pods ready")
        
        return findings
    
    async def execute_remediation(self, strategy: str, service: str) -> bool:
        """Execute remediation using infrastructure APIs"""
        
        print(f"\n⚡ EXECUTING REMEDIATION: {strategy}\n")
        
        if strategy == "scale_up":
            # Create incident
            incident_id = await self.pagerduty.create_incident(
                type('obj', (object,), {'message': f'Scaling up {service}'}),
                severity="high"
            )
            
            # Scale deployment
            success = await self.kubernetes.scale_deployment(service, replicas=8)
            
            # Update incident
            if success:
                await self.pagerduty.update_incident(
                    incident_id, 
                    status="resolved",
                    note="Auto-remediated by scaling deployment"
                )
            
            return success
        
        elif strategy == "rollback":
            # Create incident
            incident_id = await self.pagerduty.create_incident(
                type('obj', (object,), {'message': f'Rolling back {service}'}),
                severity="critical"
            )
            
            # Rollback
            success = await self.kubernetes.rollback_deployment(service)
            
            # Update incident
            if success:
                await self.pagerduty.update_incident(
                    incident_id,
                    status="resolved",
                    note="Auto-remediated by deployment rollback"
                )
            
            return success
        
        elif strategy == "restart":
            success = await self.kubernetes.restart_pods(service, strategy="rolling")
            return success
        
        return False


async def demo_integrated_system():
    """Demonstrate integrated system"""
    
    from autonomous_first_responder import Alert, Severity
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           AUTONOMOUS FIRST RESPONDER - INTEGRATED DEMO                       ║
║                                                                              ║
║  Integrations:                                                               ║
║    • Prometheus - Metrics and alerting                                       ║
║    • Elasticsearch - Log aggregation and search                              ║
║    • Kubernetes - Container orchestration                                    ║
║    • PagerDuty - Incident management                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    responder = IntegratedFirstResponder()
    
    # Create alert
    alert = Alert(
        id="INC-2024-INT-001",
        timestamp=datetime.now(),
        service="payment-service",
        severity=Severity.CRITICAL,
        message="High error rate and latency spike detected",
        metadata={"source": "prometheus"}
    )
    
    # Investigate with real integrations
    findings = await responder.investigate_with_real_data(alert)
    
    # Determine and execute remediation
    print("\n" + "="*80)
    print("REMEDIATION DECISION")
    print("="*80 + "\n")
    
    # Simple decision logic based on findings
    if findings["kubernetes"]["replicas"]["unavailable"] > 1:
        print("Decision: RESTART unhealthy pods\n")
        success = await responder.execute_remediation("restart", alert.service)
    elif findings["metrics"]["cpu_usage"] > 80:
        print("Decision: SCALE UP deployment\n")
        success = await responder.execute_remediation("scale_up", alert.service)
    else:
        print("Decision: ROLLBACK to previous version\n")
        success = await responder.execute_remediation("rollback", alert.service)
    
    print(f"\n{'='*80}")
    print(f"REMEDIATION: {'SUCCESS ✅' if success else 'FAILED ❌'}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(demo_integrated_system())
