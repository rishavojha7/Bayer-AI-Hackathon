from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import operator
from datetime import datetime

# ==================== STATE DEFINITIONS ====================

class IncidentState(TypedDict):
    """Main state object tracking the incident investigation"""
    # Core incident data
    alert_id: str
    alert_description: str
    severity: str
    timestamp: str
    
    # Reasoning loop stage
    stage: Literal["DETECT", "PLAN", "INVESTIGATE", "DECIDE", "ACT", "REPORT"]
    
    # Investigation plan
    investigation_plan: list[str]
    
    # Agent findings
    metrics_findings: dict
    logs_findings: dict
    deploy_findings: dict
    
    # Analysis results
    root_cause: str
    confidence_score: float
    remediation_actions: list[str]
    
    # Conversation history
    messages: Annotated[list, operator.add]
    
    # Control flow
    next_action: str
    investigation_complete: bool
    max_iterations: int
    current_iteration: int


# ==================== AGENT IMPLEMENTATIONS ====================

class CommanderAgent:
    """Orchestrator that evaluates alerts and develops investigation plans"""
    
    def detect(self, state: IncidentState) -> IncidentState:
        """DETECT phase: Analyze initial alert and categorize severity"""
        print(f"\n🚨 COMMANDER: Detecting incident {state['alert_id']}")
        print(f"   Alert: {state['alert_description']}")
        print(f"   Severity: {state['severity']}")
        
        state["messages"].append(
            SystemMessage(content=f"[DETECT] Incident detected: {state['alert_description']}")
        )
        state["stage"] = "PLAN"
        state["next_action"] = "plan"
        return state
    
    def plan(self, state: IncidentState) -> IncidentState:
        """PLAN phase: Develop investigation strategy"""
        print("\n📋 COMMANDER: Formulating investigation plan...")
        
        # Create investigation plan based on alert type
        investigation_plan = [
            "Analyze system metrics for anomalies",
            "Scan application logs for error patterns",
            "Check recent deployments and configuration changes",
            "Correlate findings across all data sources"
        ]
        
        state["investigation_plan"] = investigation_plan
        state["stage"] = "INVESTIGATE"
        state["next_action"] = "investigate_metrics"
        
        print("   Investigation Plan:")
        for i, step in enumerate(investigation_plan, 1):
            print(f"   {i}. {step}")
        
        state["messages"].append(
            SystemMessage(content=f"[PLAN] Investigation plan created with {len(investigation_plan)} steps")
        )
        return state
    
    def decide(self, state: IncidentState) -> IncidentState:
        """DECIDE phase: Analyze findings and determine root cause"""
        print("\n🧠 COMMANDER: Analyzing findings and determining root cause...")
        
        # Synthesize findings from all agents
        metrics = state.get("metrics_findings", {})
        logs = state.get("logs_findings", {})
        deploy = state.get("deploy_findings", {})
        
        # Simple root cause analysis logic
        confidence = 0.0
        root_cause = "Unknown"
        
        if deploy.get("recent_deployment"):
            root_cause = f"Recent deployment at {deploy.get('deployment_time')} likely caused the issue"
            confidence = 0.85
        elif logs.get("error_count", 0) > 100:
            root_cause = f"High error rate detected: {logs.get('primary_error_type')}"
            confidence = 0.75
        elif metrics.get("cpu_spike") or metrics.get("memory_spike"):
            root_cause = "Resource exhaustion detected in system metrics"
            confidence = 0.70
        else:
            root_cause = "Multiple factors detected - requires deeper investigation"
            confidence = 0.50
        
        state["root_cause"] = root_cause
        state["confidence_score"] = confidence
        state["stage"] = "ACT"
        state["next_action"] = "act"
        
        print(f"   Root Cause: {root_cause}")
        print(f"   Confidence: {confidence*100:.1f}%")
        
        state["messages"].append(
            SystemMessage(content=f"[DECIDE] Root cause identified with {confidence*100:.1f}% confidence")
        )
        return state
    
    def act(self, state: IncidentState) -> IncidentState:
        """ACT phase: Determine and initiate remediation actions"""
        print("\n⚡ COMMANDER: Initiating remediation actions...")
        
        # Determine remediation based on root cause
        remediation_actions = []
        
        if "deployment" in state["root_cause"].lower():
            remediation_actions = [
                "Initiate rollback to previous stable version",
                "Notify deployment team",
                "Create incident ticket with deployment details"
            ]
        elif "error rate" in state["root_cause"].lower():
            remediation_actions = [
                "Scale up application instances",
                "Enable circuit breaker patterns",
                "Alert development team for bug fix"
            ]
        elif "resource" in state["root_cause"].lower():
            remediation_actions = [
                "Auto-scale infrastructure resources",
                "Clear cache and temporary files",
                "Restart affected services"
            ]
        else:
            remediation_actions = [
                "Escalate to on-call engineer",
                "Collect additional diagnostics",
                "Monitor for pattern evolution"
            ]
        
        state["remediation_actions"] = remediation_actions
        state["stage"] = "REPORT"
        state["next_action"] = "report"
        
        print("   Remediation Actions:")
        for i, action in enumerate(remediation_actions, 1):
            print(f"   {i}. {action}")
        
        state["messages"].append(
            SystemMessage(content=f"[ACT] {len(remediation_actions)} remediation actions initiated")
        )
        return state
    
    def report(self, state: IncidentState) -> IncidentState:
        """REPORT phase: Generate comprehensive incident report"""
        print("\n📊 COMMANDER: Generating incident report...")
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           AUTONOMOUS INCIDENT COMMANDER - REPORT             ║
╚══════════════════════════════════════════════════════════════╝

INCIDENT DETAILS:
  ID: {state['alert_id']}
  Timestamp: {state['timestamp']}
  Severity: {state['severity']}
  Description: {state['alert_description']}

ROOT CAUSE ANALYSIS:
  Finding: {state['root_cause']}
  Confidence: {state['confidence_score']*100:.1f}%

INVESTIGATION SUMMARY:
  Metrics Findings:
    - CPU Anomaly: {state.get('metrics_findings', {}).get('cpu_spike', 'None')}
    - Memory Anomaly: {state.get('metrics_findings', {}).get('memory_spike', 'None')}
    - Latency Issue: {state.get('metrics_findings', {}).get('latency_spike', 'None')}
  
  Logs Findings:
    - Error Count: {state.get('logs_findings', {}).get('error_count', 0)}
    - Primary Error: {state.get('logs_findings', {}).get('primary_error_type', 'N/A')}
  
  Deployment History:
    - Recent Deployment: {state.get('deploy_findings', {}).get('recent_deployment', False)}
    - Config Changes: {state.get('deploy_findings', {}).get('config_changes', False)}

REMEDIATION ACTIONS:
{chr(10).join(f'  {i}. {action}' for i, action in enumerate(state['remediation_actions'], 1))}

STATUS: Investigation Complete ✓
        """
        
        print(report)
        
        state["investigation_complete"] = True
        state["next_action"] = "end"
        state["messages"].append(
            SystemMessage(content="[REPORT] Incident report generated and filed")
        )
        
        return state


class MetricsAgent:
    """Telemetry analyst focused on performance counters"""
    
    def analyze_metrics(self, state: IncidentState) -> IncidentState:
        """Analyze system metrics for anomalies"""
        print("\n📈 METRICS AGENT: Analyzing system telemetry...")
        
        # Simulate metrics analysis
        # In production, this would query Prometheus, Datadog, CloudWatch, etc.
        import random
        
        metrics_findings = {
            "cpu_spike": random.choice([True, False]),
            "cpu_value": random.randint(60, 95),
            "memory_spike": random.choice([True, False]),
            "memory_value": random.randint(70, 90),
            "latency_spike": random.choice([True, False]),
            "latency_p95": random.randint(500, 2000),
            "disk_io_issue": random.choice([True, False]),
            "network_anomaly": False,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        state["metrics_findings"] = metrics_findings
        state["next_action"] = "investigate_logs"
        
        print(f"   CPU Usage: {metrics_findings['cpu_value']}% {'⚠️ SPIKE' if metrics_findings['cpu_spike'] else '✓'}")
        print(f"   Memory Usage: {metrics_findings['memory_value']}% {'⚠️ SPIKE' if metrics_findings['memory_spike'] else '✓'}")
        print(f"   P95 Latency: {metrics_findings['latency_p95']}ms {'⚠️ SPIKE' if metrics_findings['latency_spike'] else '✓'}")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-METRICS] Metrics analysis complete")
        )
        
        return state


class LogsAgent:
    """Forensic expert that scans distributed logs"""
    
    def analyze_logs(self, state: IncidentState) -> IncidentState:
        """Scan logs for error patterns and stack traces"""
        print("\n📜 LOGS AGENT: Scanning distributed logs...")
        
        import random
        
        error_types = [
            "NullPointerException",
            "OutOfMemoryError",
            "ConnectionTimeoutException",
            "DatabaseConnectionError",
            "ServiceUnavailableException"
        ]
        
        logs_findings = {
            "error_count": random.randint(50, 500),
            "primary_error_type": random.choice(error_types),
            "stack_trace_found": True,
            "affected_services": random.randint(1, 5),
            "error_rate_trend": random.choice(["increasing", "stable", "decreasing"]),
            "first_occurrence": "2026-02-06T10:30:00Z",
            "correlation_id": f"corr-{random.randint(1000, 9999)}"
        }
        
        state["logs_findings"] = logs_findings
        state["next_action"] = "investigate_deploy"
        
        print(f"   Error Count: {logs_findings['error_count']} {'🔥' if logs_findings['error_count'] > 100 else '⚠️'}")
        print(f"   Primary Error: {logs_findings['primary_error_type']}")
        print(f"   Affected Services: {logs_findings['affected_services']}")
        print(f"   Trend: {logs_findings['error_rate_trend']}")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-LOGS] Log analysis complete - {logs_findings['error_count']} errors found")
        )
        
        return state


class DeployIntelligenceAgent:
    """Historian that maps errors against CI/CD timelines"""
    
    def analyze_deployments(self, state: IncidentState) -> IncidentState:
        """Check deployment history and configuration changes"""
        print("\n🚀 DEPLOY INTELLIGENCE: Analyzing deployment timeline...")
        
        # Simulate deployment history analysis
        # In production, this would query Jenkins, GitLab CI, GitHub Actions, etc.
        import random
        from datetime import timedelta
        
        # Check if there was a recent deployment
        recent_deployment = random.choice([True, False])
        
        deploy_findings = {
            "recent_deployment": recent_deployment,
            "deployment_time": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat() if recent_deployment else None,
            "deployment_id": f"deploy-{random.randint(1000, 9999)}" if recent_deployment else None,
            "config_changes": random.choice([True, False]),
            "rollback_available": recent_deployment,
            "previous_stable_version": "v1.2.3" if recent_deployment else None,
            "deployment_method": random.choice(["blue-green", "rolling", "canary"]) if recent_deployment else None
        }
        
        state["deploy_findings"] = deploy_findings
        state["next_action"] = "decide"
        
        if recent_deployment:
            print(f"   🔴 Recent Deployment Detected!")
            print(f"   Time: {deploy_findings['deployment_time']}")
            print(f"   ID: {deploy_findings['deployment_id']}")
            print(f"   Method: {deploy_findings['deployment_method']}")
            print(f"   Rollback Available: {'Yes ✓' if deploy_findings['rollback_available'] else 'No'}")
        else:
            print(f"   ✓ No recent deployments in investigation window")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-DEPLOY] Deployment analysis complete")
        )
        
        return state


# ==================== GRAPH BUILDER ====================

def create_incident_commander_graph():
    """Build the complete Autonomous Incident Commander graph"""
    
    # Initialize agents
    commander = CommanderAgent()
    metrics_agent = MetricsAgent()
    logs_agent = LogsAgent()
    deploy_agent = DeployIntelligenceAgent()
    
    # Create the graph
    workflow = StateGraph(IncidentState)
    
    # Add nodes for each phase
    workflow.add_node("detect", commander.detect)
    workflow.add_node("plan", commander.plan)
    workflow.add_node("investigate_metrics", metrics_agent.analyze_metrics)
    workflow.add_node("investigate_logs", logs_agent.analyze_logs)
    workflow.add_node("investigate_deploy", deploy_agent.analyze_deployments)
    workflow.add_node("decide", commander.decide)
    workflow.add_node("act", commander.act)
    workflow.add_node("report", commander.report)
    
    # Define the reasoning loop flow
    workflow.add_edge(START, "detect")
    workflow.add_edge("detect", "plan")
    workflow.add_edge("plan", "investigate_metrics")
    workflow.add_edge("investigate_metrics", "investigate_logs")
    workflow.add_edge("investigate_logs", "investigate_deploy")
    workflow.add_edge("investigate_deploy", "decide")
    workflow.add_edge("decide", "act")
    workflow.add_edge("act", "report")
    workflow.add_edge("report", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# ==================== EXECUTION ====================

def run_incident_commander(alert_description: str, severity: str = "HIGH"):
    """Execute the Autonomous Incident Commander"""
    
    # Create the graph
    app = create_incident_commander_graph()
    
    # Initialize state with incident data
    initial_state = {
        "alert_id": f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "alert_description": alert_description,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
        "stage": "DETECT",
        "investigation_plan": [],
        "metrics_findings": {},
        "logs_findings": {},
        "deploy_findings": {},
        "root_cause": "",
        "confidence_score": 0.0,
        "remediation_actions": [],
        "messages": [],
        "next_action": "detect",
        "investigation_complete": False,
        "max_iterations": 10,
        "current_iteration": 0
    }
    
    print("\n" + "="*70)
    print("  AUTONOMOUS INCIDENT COMMANDER - BAYER AI HACKATHON 2026")
    print("="*70)
    
    # Execute the graph
    final_state = app.invoke(initial_state)
    
    return final_state


if __name__ == "__main__":
    # Example incident scenarios
    scenarios = [
        ("High latency detected on payment service API - P95 latency exceeds 2000ms", "CRITICAL"),
        ("Database connection pool exhausted - 503 errors increasing", "HIGH"),
        ("Memory leak suspected in order processing service", "MEDIUM"),
    ]
    
    # Run the first scenario
    result = run_incident_commander(
        alert_description=scenarios[0][0],
        severity=scenarios[0][1]
    )
    
    print("\n" + "="*70)
    print("  EXECUTION COMPLETE")
    print("="*70)


