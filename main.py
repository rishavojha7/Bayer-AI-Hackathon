from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import operator
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    def __init__(self, llm):
        self.llm = llm
    
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert incident commander. Create a detailed investigation plan."),
            ("human", """Alert: {alert_description}
Severity: {severity}

Create a structured investigation plan with 4-6 specific steps to diagnose this incident.
Return ONLY a JSON array of strings, nothing else.
Example: ["Step 1", "Step 2", "Step 3"]""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            alert_description=state["alert_description"],
            severity=state["severity"]
        ))
        
        try:
            investigation_plan = json.loads(response.content)
        except:
            # Fallback if JSON parsing fails
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert incident commander performing root cause analysis."),
            ("human", """Alert: {alert_description}

Metrics Findings:
{metrics}

Logs Findings:
{logs}

Deployment Findings:
{deploy}

Analyze all findings and determine the root cause. Return a JSON object with:
{{"root_cause": "detailed explanation", "confidence": 0.85}}
Confidence should be between 0.0 and 1.0.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            alert_description=state["alert_description"],
            metrics=json.dumps(metrics, indent=2),
            logs=json.dumps(logs, indent=2),
            deploy=json.dumps(deploy, indent=2)
        ))
        
        try:
            result = json.loads(response.content)
            root_cause = result["root_cause"]
            confidence = float(result["confidence"])
        except:
            root_cause = "Unable to determine root cause from available data"
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert incident commander determining remediation actions."),
            ("human", """Root Cause: {root_cause}
Confidence: {confidence}
Severity: {severity}

Based on this root cause analysis, determine 3-5 specific remediation actions.
Return ONLY a JSON array of action strings.
Example: ["Action 1", "Action 2", "Action 3"]""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            root_cause=state["root_cause"],
            confidence=state["confidence_score"],
            severity=state["severity"]
        ))
        
        try:
            remediation_actions = json.loads(response.content)
        except:
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
    
    def __init__(self, llm):
        self.llm = llm
    
    def analyze_metrics(self, state: IncidentState) -> IncidentState:
        """Analyze system metrics for anomalies"""
        print("\n📈 METRICS AGENT: Analyzing system telemetry...")
        
        # Simulate actual metrics data (in production, query from monitoring systems)
        import random
        simulated_metrics = {
            "cpu_usage": random.randint(60, 95),
            "memory_usage": random.randint(70, 90),
            "p95_latency_ms": random.randint(500, 2000),
            "p99_latency_ms": random.randint(1000, 3000),
            "request_rate": random.randint(100, 1000),
            "error_rate": random.uniform(0.01, 0.15),
            "disk_io_wait": random.uniform(0.1, 5.0),
            "network_throughput_mbps": random.randint(50, 500)
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert telemetry analyst. Analyze system metrics and identify anomalies."),
            ("human", """Alert: {alert_description}

Current System Metrics:
{metrics}

Analyze these metrics and identify any anomalies or concerning patterns.
Return a JSON object with your findings:
{{
  "cpu_spike": true/false,
  "cpu_value": number,
  "memory_spike": true/false,
  "memory_value": number,
  "latency_spike": true/false,
  "latency_p95": number,
  "analysis": "brief analysis",
  "anomalies_detected": ["list of anomalies"]
}}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            alert_description=state["alert_description"],
            metrics=json.dumps(simulated_metrics, indent=2)
        ))
        
        try:
            metrics_findings = json.loads(response.content)
            metrics_findings["analysis_timestamp"] = datetime.now().isoformat()
        except:
            # Fallback
            metrics_findings = {
                "cpu_spike": simulated_metrics["cpu_usage"] > 80,
                "cpu_value": simulated_metrics["cpu_usage"],
                "memory_spike": simulated_metrics["memory_usage"] > 85,
                "memory_value": simulated_metrics["memory_usage"],
                "latency_spike": simulated_metrics["p95_latency_ms"] > 1000,
                "latency_p95": simulated_metrics["p95_latency_ms"],
                "analysis": "Metrics analyzed",
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        state["metrics_findings"] = metrics_findings
        state["next_action"] = "investigate_logs"
        
        print(f"   CPU Usage: {metrics_findings.get('cpu_value', 'N/A')}% {'⚠️ SPIKE' if metrics_findings.get('cpu_spike') else '✓'}")
        print(f"   Memory Usage: {metrics_findings.get('memory_value', 'N/A')}% {'⚠️ SPIKE' if metrics_findings.get('memory_spike') else '✓'}")
        print(f"   P95 Latency: {metrics_findings.get('latency_p95', 'N/A')}ms {'⚠️ SPIKE' if metrics_findings.get('latency_spike') else '✓'}")
        if "analysis" in metrics_findings:
            print(f"   Analysis: {metrics_findings['analysis']}")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-METRICS] Metrics analysis complete")
        )
        
        return state


class LogsAgent:
    """Forensic expert that scans distributed logs"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def analyze_logs(self, state: IncidentState) -> IncidentState:
        """Scan logs for error patterns and stack traces"""
        print("\n📜 LOGS AGENT: Scanning distributed logs...")
        
        import random
        
        # Simulate log samples (in production, query from ELK, Splunk, CloudWatch Logs, etc.)
        error_samples = [
            "ERROR: Connection timeout to database after 30s",
            "WARN: Memory usage at 92% - approaching threshold",
            "ERROR: NullPointerException in OrderService.processPayment()",
            "ERROR: ServiceUnavailableException: Payment gateway not responding",
            "FATAL: OutOfMemoryError: Java heap space"
        ]
        
        simulated_log_data = {
            "error_count": random.randint(50, 500),
            "sample_errors": random.sample(error_samples, min(3, len(error_samples))),
            "time_window": "last 1 hour",
            "affected_services": random.randint(1, 5)
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert log forensics analyst. Analyze error logs and identify patterns."),
            ("human", """Alert: {alert_description}

Log Data:
Error Count: {error_count}
Time Window: {time_window}
Sample Error Messages:
{sample_errors}

Analyze these logs and identify error patterns, root causes, and trends.
Return a JSON object:
{{
  "error_count": number,
  "primary_error_type": "main error type",
  "stack_trace_found": true/false,
  "affected_services": number,
  "error_rate_trend": "increasing/stable/decreasing",
  "pattern_analysis": "detailed analysis",
  "suspected_causes": ["list of possible causes"]
}}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            alert_description=state["alert_description"],
            error_count=simulated_log_data["error_count"],
            time_window=simulated_log_data["time_window"],
            sample_errors="\n".join(simulated_log_data["sample_errors"])
        ))
        
        try:
            logs_findings = json.loads(response.content)
            logs_findings["first_occurrence"] = "2026-02-06T10:30:00Z"
            logs_findings["correlation_id"] = f"corr-{random.randint(1000, 9999)}"
        except:
            # Fallback
            logs_findings = {
                "error_count": simulated_log_data["error_count"],
                "primary_error_type": "ServiceException",
                "stack_trace_found": True,
                "affected_services": simulated_log_data["affected_services"],
                "error_rate_trend": "increasing",
                "first_occurrence": "2026-02-06T10:30:00Z",
                "correlation_id": f"corr-{random.randint(1000, 9999)}"
            }
        
        state["logs_findings"] = logs_findings
        state["next_action"] = "investigate_deploy"
        
        print(f"   Error Count: {logs_findings['error_count']} {'🔥' if logs_findings['error_count'] > 100 else '⚠️'}")
        print(f"   Primary Error: {logs_findings.get('primary_error_type', 'N/A')}")
        print(f"   Affected Services: {logs_findings.get('affected_services', 'N/A')}")
        print(f"   Trend: {logs_findings.get('error_rate_trend', 'N/A')}")
        if "pattern_analysis" in logs_findings:
            print(f"   Pattern: {logs_findings['pattern_analysis']}")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-LOGS] Log analysis complete - {logs_findings['error_count']} errors found")
        )
        
        return state


class DeployIntelligenceAgent:
    """Historian that maps errors against CI/CD timelines"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def analyze_deployments(self, state: IncidentState) -> IncidentState:
        """Check deployment history and configuration changes"""
        print("\n🚀 DEPLOY INTELLIGENCE: Analyzing deployment timeline...")
        
        # Simulate deployment history (in production, query CI/CD systems)
        import random
        from datetime import timedelta
        
        recent_deployments = []
        for i in range(random.randint(1, 3)):
            recent_deployments.append({
                "deployment_id": f"deploy-{random.randint(1000, 9999)}",
                "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                "service": random.choice(["payment-service", "order-service", "user-service"]),
                "version": f"v1.{random.randint(0, 5)}.{random.randint(0, 10)}",
                "status": "completed"
            })
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert deployment analyst. Analyze deployment history and correlate with incidents."),
            ("human", """Alert: {alert_description}
Incident Time: {incident_time}

Recent Deployments:
{deployments}

Analyze if any recent deployments could be related to this incident.
Return a JSON object:
{{
  "recent_deployment": true/false,
  "deployment_time": "ISO timestamp or null",
  "deployment_id": "ID or null",
  "config_changes": true/false,
  "rollback_available": true/false,
  "correlation_analysis": "analysis of deployment correlation",
  "risk_assessment": "low/medium/high"
}}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            alert_description=state["alert_description"],
            incident_time=state["timestamp"],
            deployments=json.dumps(recent_deployments, indent=2)
        ))
        
        try:
            deploy_findings = json.loads(response.content)
        except:
            # Fallback
            has_recent = len(recent_deployments) > 0
            deploy_findings = {
                "recent_deployment": has_recent,
                "deployment_time": recent_deployments[0]["timestamp"] if has_recent else None,
                "deployment_id": recent_deployments[0]["deployment_id"] if has_recent else None,
                "config_changes": random.choice([True, False]),
                "rollback_available": has_recent,
                "previous_stable_version": "v1.2.3" if has_recent else None
            }
        
        state["deploy_findings"] = deploy_findings
        state["next_action"] = "decide"
        
        if deploy_findings.get("recent_deployment"):
            print(f"   🔴 Recent Deployment Detected!")
            print(f"   Time: {deploy_findings.get('deployment_time')}")
            print(f"   ID: {deploy_findings.get('deployment_id')}")
            if "correlation_analysis" in deploy_findings:
                print(f"   Analysis: {deploy_findings['correlation_analysis']}")
            print(f"   Rollback Available: {'Yes ✓' if deploy_findings.get('rollback_available') else 'No'}")
        else:
            print(f"   ✓ No recent deployments in investigation window")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-DEPLOY] Deployment analysis complete")
        )
        
        return state


# ==================== GRAPH BUILDER ====================

def create_incident_commander_graph():
    """Build the complete Autonomous Incident Commander graph"""
    
    # Initialize Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Initialize agents with LLM
    commander = CommanderAgent(llm)
    metrics_agent = MetricsAgent(llm)
    logs_agent = LogsAgent(llm)
    deploy_agent = DeployIntelligenceAgent(llm)
    
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


