from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import operator
from datetime import datetime
import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== STATE DEFINITIONS ====================

class IncidentState(TypedDict):
    """Main state object tracking the incident investigation"""
    # Core incident data
    incident_id: str
    timestamp_utc: str
    environment: str
    region: str
    
    # Service information
    service: dict  # {name, version, instance_count}
    
    # Trigger information
    trigger: dict  # {type, source, severity, alert_name, firing_duration_seconds}
    
    # Raw metrics snapshot
    metrics_snapshot: dict
    
    # Log signals
    log_signals: dict
    
    # Deployment context
    deployment_context: dict
    
    # Customer impact
    customer_impact: dict
    
    # Correlation IDs
    correlation_ids: dict
    
    # Log file path for analysis
    log_file_path: str
    
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
        logger.info("="*70)
        logger.info("DETECT PHASE STARTED")
        logger.info("="*70)
        print(f"\n[!] COMMANDER: Detecting incident {state['incident_id']}")
        print(f"   Service: {state['service']['name']} {state['service']['version']}")
        print(f"   Environment: {state['environment']} ({state['region']})")
        print(f"   Severity: {state['trigger']['severity']}")
        print(f"   Alert: {state['trigger']['alert_name']}")
        print(f"   Timestamp: {state['timestamp_utc']}")
        print(f"   Customer Impact: ${state['customer_impact']['revenue_impact_usd_per_min']}/min")
        logger.info(f"Incident ID: {state['incident_id']}")
        logger.info(f"Service: {state['service']['name']} v{state['service']['version']}")
        logger.info(f"Severity: {state['trigger']['severity']}")
        
        state["messages"].append(
            SystemMessage(content=f"[DETECT] Incident detected in {state['service']['name']} ({state['environment']}) - {state['trigger']['alert_name']}")
        )
        state["stage"] = "PLAN"
        state["next_action"] = "plan"
        return state
    
    def plan(self, state: IncidentState) -> IncidentState:
        """PLAN phase: Develop investigation strategy"""
        logger.info("="*70)
        logger.info("PLAN PHASE STARTED")
        logger.info("="*70)
        print("\n[PLAN] COMMANDER: Formulating investigation plan...")
        logger.info("Invoking LLM to create investigation plan...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert incident commander. Create a detailed investigation plan."),
            ("human", """Service: {service_name} v{service_version}
Environment: {environment} ({region})
Severity: {severity}
Alert: {alert_name}

Metrics Snapshot:
{metrics}

Log Signals:
{logs}

Deployment Context:
{deployment}

Customer Impact:
- Affected Requests: {affected_pct}%
- Failed Transactions: {failed_txn}
- Revenue Impact: ${revenue_impact}/min

Create a structured investigation plan with 4-6 specific steps to diagnose this incident.
Return ONLY a JSON array of strings, nothing else.
Example: ["Step 1", "Step 2", "Step 3"]""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            service_name=state["service"]["name"],
            service_version=state["service"]["version"],
            environment=state["environment"],
            region=state["region"],
            severity=state["trigger"]["severity"],
            alert_name=state["trigger"]["alert_name"],
            metrics=json.dumps(state["metrics_snapshot"], indent=2),
            logs=json.dumps(state["log_signals"], indent=2),
            deployment=json.dumps(state["deployment_context"], indent=2),
            affected_pct=state["customer_impact"]["estimated_affected_requests_pct"],
            failed_txn=state["customer_impact"]["failed_transactions_last_10min"],
            revenue_impact=state["customer_impact"]["revenue_impact_usd_per_min"]
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
        
        logger.info(f"Investigation plan created with {len(investigation_plan)} steps")
        print("   Investigation Plan:")
        for i, step in enumerate(investigation_plan, 1):
            print(f"   {i}. {step}")
            logger.debug(f"Plan step {i}: {step}")
        
        state["messages"].append(
            SystemMessage(content=f"[PLAN] Investigation plan created with {len(investigation_plan)} steps")
        )
        return state
    
    def decide(self, state: IncidentState) -> IncidentState:
        """DECIDE phase: Analyze findings and determine root cause"""
        logger.info("="*70)
        logger.info("DECIDE PHASE STARTED")
        logger.info("="*70)
        print("\n[AI] COMMANDER: Analyzing findings and determining root cause...")
        logger.info("Synthesizing findings from all agents...")
        
        # Synthesize findings from all agents
        metrics = state.get("metrics_findings", {})
        logs = state.get("logs_findings", {})
        deploy = state.get("deploy_findings", {})
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert incident commander performing root cause analysis."),
            ("human", """Service: {service_name} v{service_version}
Environment: {environment}
Alert: {alert_name}
Severity: {severity}

Customer Impact:
- Revenue Loss: ${revenue_impact}/min
- Failed Transactions: {failed_txn} in last 10min

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
            service_name=state["service"]["name"],
            service_version=state["service"]["version"],
            environment=state["environment"],
            alert_name=state["trigger"]["alert_name"],
            severity=state["trigger"]["severity"],
            revenue_impact=state["customer_impact"]["revenue_impact_usd_per_min"],
            failed_txn=state["customer_impact"]["failed_transactions_last_10min"],
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
        logger.info("="*70)
        logger.info("ACT PHASE STARTED")
        logger.info("="*70)
        print("\n[ACT] COMMANDER: Initiating remediation actions...")
        logger.info(f"Root cause: {state['root_cause']}")
        logger.info(f"Confidence: {state['confidence_score']*100:.1f}%")
        
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
            severity=state["trigger"]["severity"]
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
        logger.info("="*70)
        logger.info("REPORT PHASE STARTED")
        logger.info("="*70)
        print("\n[REPORT] COMMANDER: Generating incident report...")
        logger.info("Compiling final incident report...")
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           AUTONOMOUS INCIDENT COMMANDER - REPORT             ║
╚══════════════════════════════════════════════════════════════╝

INCIDENT DETAILS:
  Incident ID: {state['incident_id']}
  Service: {state['service']['name']} v{state['service']['version']}
  Environment: {state['environment']} ({state['region']})
  Instance Count: {state['service']['instance_count']}
  Timestamp: {state['timestamp_utc']}
  Alert: {state['trigger']['alert_name']}
  Severity: {state['trigger']['severity']}
  Firing Duration: {state['trigger']['firing_duration_seconds']}s

CUSTOMER IMPACT:
  Affected Requests: {state['customer_impact']['estimated_affected_requests_pct']}%
  Failed Transactions (10min): {state['customer_impact']['failed_transactions_last_10min']}
  Revenue Impact: ${state['customer_impact']['revenue_impact_usd_per_min']}/minute

INITIAL METRICS SNAPSHOT:
  P99 Latency: {state['metrics_snapshot'].get('p99_latency_ms', 'N/A')}ms (baseline: {state['metrics_snapshot'].get('baseline_p99_latency_ms', 'N/A')}ms)
  CPU Utilization: {state['metrics_snapshot'].get('cpu_utilization_pct', 'N/A')}%
  Memory Utilization: {state['metrics_snapshot'].get('memory_utilization_pct', 'N/A')}%
  Error Rate: {state['metrics_snapshot'].get('error_rate_pct', 'N/A')}%

LOG SIGNALS:
  Error Count (5min): {state['log_signals']['error_count_last_5min']}
  Dominant Exception: {state['log_signals']['dominant_exception']}
  Affected Endpoints: {', '.join(state['log_signals']['affected_endpoints'])}

DEPLOYMENT CONTEXT:
  Last Deploy: {state['deployment_context']['last_deploy_id']}
  Deploy Time: {state['deployment_context']['last_deploy_timestamp_utc']}
  Time Since Deploy: {state['deployment_context']['time_since_last_deploy_minutes']} minutes
  Changed Components: {', '.join(state['deployment_context']['changed_components'])}

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

STATUS: Investigation Complete [OK]
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
        logger.info("="*70)
        logger.info("METRICS ANALYSIS STARTED")
        logger.info("="*70)
        print("\n[METRICS] METRICS AGENT: Analyzing system telemetry...")
        logger.info("Analyzing metrics snapshot...")
        
        # Get metrics snapshot from the incident
        metrics_snapshot = state["metrics_snapshot"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert telemetry analyst. Analyze system metrics and identify anomalies."),
            ("human", """Service: {service_name} v{service_version}
Environment: {environment}
Instance Count: {instance_count}
Severity: {severity}
Alert: {alert_name}

Metrics Snapshot:
{metrics}

Analyze these metrics and identify any anomalies or concerning patterns.
Consider the baseline values and current readings.
Return a JSON object with your findings:
{{
  "latency_spike": true/false,
  "latency_p99": number,
  "baseline_p99": number,
  "latency_increase_pct": number,
  "cpu_utilization_high": true/false,
  "cpu_value": number,
  "memory_utilization_high": true/false,
  "memory_value": number,
  "error_rate_elevated": true/false,
  "error_rate_pct": number,
  "analysis": "brief analysis",
  "anomalies_detected": ["list of anomalies"],
  "critical_issues": ["list of critical issues"]
}}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            service_name=state["service"]["name"],
            service_version=state["service"]["version"],
            environment=state["environment"],
            instance_count=state["service"]["instance_count"],
            severity=state["trigger"]["severity"],
            alert_name=state["trigger"]["alert_name"],
            metrics=json.dumps(metrics_snapshot, indent=2)
        ))
        
        try:
            metrics_findings = json.loads(response.content)
            metrics_findings["analysis_timestamp"] = datetime.now().isoformat()
        except:
            # Fallback using actual metrics_snapshot
            metrics_findings = {
                "latency_spike": metrics_snapshot.get("p99_latency_ms", 0) > metrics_snapshot.get("baseline_p99_latency_ms", 0) * 2,
                "latency_p99": metrics_snapshot.get("p99_latency_ms", 0),
                "baseline_p99": metrics_snapshot.get("baseline_p99_latency_ms", 0),
                "cpu_utilization_high": metrics_snapshot.get("cpu_utilization_pct", 0) > 80,
                "cpu_value": metrics_snapshot.get("cpu_utilization_pct", 0),
                "memory_utilization_high": metrics_snapshot.get("memory_utilization_pct", 0) > 85,
                "memory_value": metrics_snapshot.get("memory_utilization_pct", 0),
                "error_rate_elevated": metrics_snapshot.get("error_rate_pct", 0) > 2,
                "error_rate_pct": metrics_snapshot.get("error_rate_pct", 0),
                "analysis": "Metrics analyzed",
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        state["metrics_findings"] = metrics_findings
        state["next_action"] = "investigate_logs"
        
        print(f"   P99 Latency: {metrics_findings.get('latency_p99', 'N/A')}ms (baseline: {metrics_findings.get('baseline_p99', 'N/A')}ms) {'[WARN] SPIKE' if metrics_findings.get('latency_spike') else '[OK]'}")
        print(f"   CPU Utilization: {metrics_findings.get('cpu_value', 'N/A')}% {'[WARN] HIGH' if metrics_findings.get('cpu_utilization_high') else '[OK]'}")
        print(f"   Memory Utilization: {metrics_findings.get('memory_value', 'N/A')}% {'[WARN] HIGH' if metrics_findings.get('memory_utilization_high') else '[OK]'}")
        print(f"   Error Rate: {metrics_findings.get('error_rate_pct', 'N/A')}% {'[WARN] ELEVATED' if metrics_findings.get('error_rate_elevated') else '[OK]'}")
        if "analysis" in metrics_findings:
            print(f"   Analysis: {metrics_findings['analysis']}")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-METRICS] Metrics analysis complete")
        )
        
        return state


class LogsAgent:
    """Forensic expert that scans distributed logs using streaming analysis"""
    
    def __init__(self, llm):
        self.llm = llm
        # Import our log analyzer
        from log_analyzer import (
            StreamingLogAnalyzer, 
            IsolationForestAnalyzer,
            load_baseline_stats, 
            save_baseline_stats
        )
        self.analyzer = StreamingLogAnalyzer()
        self.iso_forest = IsolationForestAnalyzer(contamination=0.05)  # Expect 5% anomalies
        self.baseline_stats_file = 'baseline_stats.json'
        self.iso_forest_model_file = 'iso_forest_model.joblib'
        self.baseline_stats = load_baseline_stats(self.baseline_stats_file)
        
        # Try to load pre-trained Isolation Forest model
        if self.baseline_stats:
            try:
                self.iso_forest.load_model(self.iso_forest_model_file)
            except:
                # Train if model doesn't exist
                if len(self.baseline_stats) >= 10:
                    print("   [AI] Training Isolation Forest model...")
                    self.iso_forest.train_on_baseline(self.baseline_stats)
                    self.iso_forest.save_model(self.iso_forest_model_file)
    
    def analyze_logs(self, state: IncidentState) -> IncidentState:
        """Scan logs for error patterns using streaming analysis and anomaly detection"""
        logger.info("="*70)
        logger.info("LOG ANALYSIS STARTED")
        logger.info("="*70)
        print("\n[LOGS] LOGS AGENT: Scanning distributed logs with anomaly detection...")
        logger.info("Starting log analysis with anomaly detection...")
        
        # Check if we have a log file to analyze
        log_file_path = state.get('log_file_path', None)
        logger.info(f"Log file path: {log_file_path}")
        
        if not log_file_path:
            logger.warning("No log file provided, using simulated analysis")
            # Fallback to simulated analysis if no log file provided
            return self._analyze_simulated_logs(state)
        
        # If no baseline exists, create one first (Training Mode)
        if not self.baseline_stats:
            print("   [REFRESH] No baseline found. Entering TRAINING mode...")
            self.baseline_stats = self.analyzer.calculate_baseline_stats(
                log_file_path,
                duration_field='duration_ms',
                message_field='message'
            )
            
            if self.baseline_stats:
                from log_analyzer import save_baseline_stats
                save_baseline_stats(self.baseline_stats, self.baseline_stats_file)
                print(f"   [OK] Baseline created with {len(self.baseline_stats)} templates")
                
                # Train Isolation Forest on new baseline
                if len(self.baseline_stats) >= 10:
                    print("   [AI] Training Isolation Forest model...")
                    self.iso_forest.train_on_baseline(self.baseline_stats)
                    self.iso_forest.save_model(self.iso_forest_model_file)
            else:
                print("   [WARN] Could not create baseline - using simulated analysis")
                return self._analyze_simulated_logs(state)
        
        # Detect anomalies using Z-score + Isolation Forest
        print("   [SEARCH] Running hybrid anomaly detection (Z-Score + Isolation Forest)...")
        logger.info("Running hybrid anomaly detection (Z-Score + Isolation Forest)...")
        anomalies = self.analyzer.detect_anomalies(
            log_file_path,
            self.baseline_stats,
            z_score_threshold=3.0,
            duration_field='duration_ms',
            message_field='message',
            session_id_field='correlation_id',  # Enable session tracking
            use_isolation_forest=True,  # Enable Isolation Forest
            iso_forest_model=self.iso_forest  # Pass trained model
        )
        
        # Analyze anomalies with LLM
        if anomalies:
            logger.info(f"Found {len(anomalies)} anomalies, selecting top 10 for LLM analysis")
            # Limit to top 10 most severe anomalies for LLM analysis
            top_anomalies = sorted(
                anomalies, 
                key=lambda x: abs(x.get('z_score', 0)) if x.get('z_score') else 0,
                reverse=True
            )[:10]
            
            anomaly_summary = self._format_anomalies_for_llm(top_anomalies)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert log forensics analyst. Analyze detected anomalies and identify patterns."),
                ("human", """Alert: {alert_description}

Detected Anomalies (Z-Score Analysis):
{anomalies}

Total Anomalies Found: {anomaly_count}
Baseline Templates: {template_count}

Analyze these anomalies and provide insights.
Return a JSON object:
{{
  "error_count": number,
  "primary_error_type": "main error type",
  "anomaly_patterns": ["list of patterns"],
  "affected_services": number,
  "error_rate_trend": "increasing/stable/decreasing",
  "pattern_analysis": "detailed analysis",
  "suspected_causes": ["list of possible causes"],
  "severity_assessment": "low/medium/high/critical"
}}""")
            ])
            
            logger.info("Invoking LLM for anomaly analysis...")
            response = self.llm.invoke(prompt.format_messages(
                alert_description=state["trigger"]["alert_name"],
                anomalies=anomaly_summary,
                anomaly_count=len(anomalies),
                template_count=len(self.baseline_stats)
            ))
            logger.info("LLM analysis complete")
            
            try:
                logs_findings = json.loads(response.content)
                logs_findings["anomalies_detected"] = len(anomalies)
                logs_findings["top_anomalies"] = top_anomalies[:5]  # Store top 5
                logs_findings["analysis_method"] = "z_score_streaming"
                logs_findings["baseline_templates"] = len(self.baseline_stats)
            except:
                logs_findings = self._create_fallback_findings(anomalies)
        else:
            # No anomalies detected
            logs_findings = {
                "error_count": 0,
                "primary_error_type": "None",
                "anomaly_patterns": [],
                "affected_services": 0,
                "error_rate_trend": "stable",
                "pattern_analysis": "No significant anomalies detected in logs",
                "suspected_causes": [],
                "severity_assessment": "low",
                "anomalies_detected": 0,
                "analysis_method": "z_score_streaming",
                "baseline_templates": len(self.baseline_stats)
            }
        
        state["logs_findings"] = logs_findings
        state["next_action"] = "investigate_deploy"
        
        # Print summary
        print(f"   Anomalies Detected: {len(anomalies)} {'[CRITICAL]' if len(anomalies) > 10 else '[WARN]' if len(anomalies) > 0 else '[OK]'}")
        print(f"   Baseline Templates: {len(self.baseline_stats)}")
        if anomalies:
            print(f"   Primary Pattern: {logs_findings.get('primary_error_type', 'N/A')}")
            print(f"   Severity: {logs_findings.get('severity_assessment', 'N/A').upper()}")
            if "pattern_analysis" in logs_findings:
                print(f"   Analysis: {logs_findings['pattern_analysis'][:100]}...")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-LOGS] Anomaly detection complete - {len(anomalies)} anomalies found using Z-score analysis")
        )
        
        return state
    
    def _format_anomalies_for_llm(self, anomalies: list) -> str:
        """Format anomalies with context for LLM consumption"""
        formatted = []
        for i, anomaly in enumerate(anomalies, 1):
            # Format the anomaly itself
            if anomaly.get('anomaly_type') == 'NEW_PATTERN':
                anomaly_desc = (
                    f"{i}. [NEW] NEW PATTERN DETECTED\n"
                    f"   Template: {anomaly['template']}\n"
                    f"   Duration: {anomaly['duration']}ms\n"
                    f"   Severity: {anomaly['severity']}\n"
                    f"   Timestamp: {anomaly.get('timestamp', 'N/A')}"
                )
            else:
                anomaly_desc = (
                    f"{i}. [WARN] {anomaly['anomaly_type']}\n"
                    f"   Template: {anomaly['template']}\n"
                    f"   Duration: {anomaly['duration']}ms (Expected: {anomaly['expected_mean']:.1f}ms ± {anomaly['expected_std']:.1f}ms)\n"
                    f"   Z-Score: {anomaly['z_score']:.2f} (Deviation: {abs(anomaly['z_score']) * anomaly['expected_std']:.0f}ms)\n"
                    f"   Severity: {anomaly['severity']}\n"
                    f"   Timestamp: {anomaly.get('timestamp', 'N/A')}"
                )
            
            # Add context if available
            context = anomaly.get('context', {})
            if context:
                # Format previous logs
                prev_logs = context.get('previous_logs', [])
                if prev_logs:
                    anomaly_desc += "\n\n   [LOGS] PREVIOUS CONTEXT (Last 5 logs before anomaly):"
                    for j, log in enumerate(prev_logs[-5:], 1):
                        anomaly_desc += f"\n      -{j}. [{log.get('level', 'INFO')}] {log.get('message', 'N/A')[:80]} ({log.get('duration_ms', 0)}ms)"
                
                # Current log
                current = context.get('current_log', {})
                if current:
                    anomaly_desc += f"\n\n   [TARGET] ANOMALY LOG:"
                    anomaly_desc += f"\n      [ACT] [{current.get('level', 'ERROR')}] {current.get('message', 'N/A')} ({current.get('duration_ms', 0)}ms)"
                
                # Format next logs
                next_logs = context.get('next_logs', [])
                if next_logs:
                    anomaly_desc += "\n\n   [LOGS] AFTERMATH (Next 5 logs after anomaly):"
                    for j, log in enumerate(next_logs[:5], 1):
                        anomaly_desc += f"\n      +{j}. [{log.get('level', 'INFO')}] {log.get('message', 'N/A')[:80]} ({log.get('duration_ms', 0)}ms)"
            
            formatted.append(anomaly_desc)
        
        return "\n\n" + "="*80 + "\n\n".join(formatted)
    
    def _create_fallback_findings(self, anomalies: list) -> dict:
        """Create fallback findings if LLM parsing fails"""
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for a in anomalies:
            severity_counts[a.get('severity', 'MEDIUM')] += 1
        
        return {
            "error_count": len(anomalies),
            "primary_error_type": "Multiple anomalies detected",
            "anomaly_patterns": list(set(a['template'] for a in anomalies[:5])),
            "affected_services": 1,
            "error_rate_trend": "increasing",
            "pattern_analysis": f"Detected {len(anomalies)} anomalies via Z-score analysis",
            "suspected_causes": ["Performance degradation", "Resource exhaustion"],
            "severity_assessment": "high" if severity_counts['HIGH'] > 0 else "medium",
            "anomalies_detected": len(anomalies),
            "analysis_method": "z_score_streaming",
            "top_anomalies": anomalies[:5]
        }
    
    def _analyze_simulated_logs(self, state: IncidentState) -> IncidentState:
        """Fallback to simulated log analysis if no real logs available"""
        print("   [WARN] No log file provided - using simulated analysis")
        
        import random
        
        # Get log signals from state
        log_signals = state.get("log_signals", {})
        
        # Simulate log samples
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
            ("human", """Service: {service_name} v{service_version}
Environment: {environment}
Severity: {severity}
Alert: {alert_name}

Log Signals:
Error Count (last 5min): {error_count}
Dominant Exception: {exception}
Stack Trace Hash: {stack_hash}
Affected Endpoints: {endpoints}

Additional Context:
{log_signals}

Analyze these logs and identify error patterns, root causes, and trends.
Return a JSON object:
{{
  "error_count": number,
  "dominant_exception": "exception type",
  "exception_category": "memory/connection/timeout/other",
  "stack_trace_analyzed": true/false,
  "affected_endpoints": ["list of endpoints"],
  "affected_endpoint_count": number,
  "error_rate_trend": "increasing/stable/decreasing",
  "pattern_analysis": "detailed analysis",
  "suspected_causes": ["list of possible causes"],
  "oom_detected": true/false
}}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            service_name=state["service"]["name"],
            service_version=state["service"]["version"],
            environment=state["environment"],
            severity=state["trigger"]["severity"],
            alert_name=state["trigger"]["alert_name"],
            error_count=log_signals.get("error_count_last_5min", 0),
            exception=log_signals.get("dominant_exception", "Unknown"),
            stack_hash=log_signals.get("sample_stack_trace_hash", "N/A"),
            endpoints=", ".join(log_signals.get("affected_endpoints", [])),
            log_signals=json.dumps(log_signals, indent=2)
        ))
        
        try:
            logs_findings = json.loads(response.content)
            logs_findings["correlation_id"] = state["correlation_ids"].get("trace_id_sample")
            logs_findings["analysis_method"] = "simulated"
        except:
            # Fallback using actual log_signals
            logs_findings = {
                "error_count": log_signals.get("error_count_last_5min", 0),
                "dominant_exception": log_signals.get("dominant_exception", "Unknown"),
                "exception_category": "memory" if "OutOfMemory" in log_signals.get("dominant_exception", "") else "other",
                "stack_trace_analyzed": True,
                "affected_endpoints": log_signals.get("affected_endpoints", []),
                "affected_endpoint_count": len(log_signals.get("affected_endpoints", [])),
                "error_rate_trend": "increasing",
                "oom_detected": "OutOfMemory" in log_signals.get("dominant_exception", ""),
                "correlation_id": state["correlation_ids"].get("trace_id_sample"),
                "analysis_method": "simulated"
            }
        
        state["logs_findings"] = logs_findings
        state["next_action"] = "investigate_deploy"
        
        print(f"   Error Count: {logs_findings['error_count']} {'[CRITICAL]' if logs_findings['error_count'] > 1000 else '[WARN]'}")
        print(f"   Dominant Exception: {logs_findings.get('dominant_exception', 'N/A')}")
        print(f"   Affected Endpoints: {logs_findings.get('affected_endpoint_count', 'N/A')} endpoints")
        print(f"   Trend: {logs_findings.get('error_rate_trend', 'N/A')}")
        if logs_findings.get('oom_detected'):
            print(f"   [!] OOM DETECTED - Memory exhaustion likely")
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
        logger.info("="*70)
        logger.info("DEPLOYMENT ANALYSIS STARTED")
        logger.info("="*70)
        print("\n[DEPLOY] DEPLOY INTELLIGENCE: Analyzing deployment timeline...")
        logger.info("Analyzing deployment context...")
        
        # Get deployment context from the incident
        deployment_ctx = state["deployment_context"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert deployment analyst. Analyze deployment history and correlate with incidents."),
            ("human", """Service: {service_name} v{service_version}
Environment: {environment}
Incident Time: {incident_time}
Alert Firing Duration: {firing_duration}s

Deployment Context:
Last Deploy ID: {deploy_id}
Last Deploy Time: {deploy_time}
Time Since Deploy: {time_since_deploy} minutes
Changed Components: {changed_components}
Config Changes: {config_changes}

Full Context:
{deployment_context}

Analyze if this deployment is related to the incident.
Return a JSON object:
{{
  "deployment_related": true/false,
  "deployment_id": "ID",
  "deployment_time": "ISO timestamp",
  "time_since_deploy_minutes": number,
  "changed_components": ["list"],
  "config_changes_detected": true/false,
  "risky_config_changes": ["list of risky changes"],
  "rollback_recommended": true/false,
  "correlation_analysis": "detailed analysis",
  "risk_assessment": "low/medium/high/critical"
}}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            service_name=state["service"]["name"],
            service_version=state["service"]["version"],
            environment=state["environment"],
            incident_time=state["timestamp_utc"],
            firing_duration=state["trigger"]["firing_duration_seconds"],
            deploy_id=deployment_ctx.get("last_deploy_id"),
            deploy_time=deployment_ctx.get("last_deploy_timestamp_utc"),
            time_since_deploy=deployment_ctx.get("time_since_last_deploy_minutes"),
            changed_components=", ".join(deployment_ctx.get("changed_components", [])),
            config_changes=json.dumps(deployment_ctx.get("config_changes", []), indent=2),
            deployment_context=json.dumps(deployment_ctx, indent=2)
        ))
        
        try:
            deploy_findings = json.loads(response.content)
        except:
            # Fallback using actual deployment_context
            deploy_findings = {
                "deployment_related": deployment_ctx.get("time_since_last_deploy_minutes", 999) < 60,
                "deployment_id": deployment_ctx.get("last_deploy_id"),
                "deployment_time": deployment_ctx.get("last_deploy_timestamp_utc"),
                "time_since_deploy_minutes": deployment_ctx.get("time_since_last_deploy_minutes"),
                "changed_components": deployment_ctx.get("changed_components", []),
                "config_changes_detected": len(deployment_ctx.get("config_changes", [])) > 0,
                "risky_config_changes": [c["key"] for c in deployment_ctx.get("config_changes", [])],
                "rollback_recommended": deployment_ctx.get("time_since_last_deploy_minutes", 999) < 60,
                "risk_assessment": "high" if deployment_ctx.get("time_since_last_deploy_minutes", 999) < 30 else "medium"
            }
        
        state["deploy_findings"] = deploy_findings
        state["next_action"] = "decide"
        
        if deploy_findings.get("deployment_related"):
            print(f"   🔴 DEPLOYMENT CORRELATION DETECTED!")
            print(f"   Deploy ID: {deploy_findings.get('deployment_id')}")
            print(f"   Deploy Time: {deploy_findings.get('deployment_time')}")
            print(f"   Time Since Deploy: {deploy_findings.get('time_since_deploy_minutes')} minutes")
            print(f"   Changed Components: {', '.join(deploy_findings.get('changed_components', []))}")
            if deploy_findings.get('config_changes_detected'):
                print(f"   [!] Config Changes: {', '.join(deploy_findings.get('risky_config_changes', []))}")
            print(f"   Risk Assessment: {deploy_findings.get('risk_assessment', 'N/A').upper()}")
            print(f"   Rollback Recommended: {'YES [WARN]' if deploy_findings.get('rollback_recommended') else 'No'}")
            if "correlation_analysis" in deploy_findings:
                print(f"   Analysis: {deploy_findings['correlation_analysis']}")
        else:
            print(f"   [OK] No deployment correlation detected")
        
        state["messages"].append(
            SystemMessage(content=f"[INVESTIGATE-DEPLOY] Deployment analysis complete")
        )
        
        return state


# ==================== GRAPH BUILDER ====================

def create_incident_commander_graph():
    """Build the complete Autonomous Incident Commander graph"""
    
    # Initialize Gemini LLM with SSL verification bypassed for corporate networks
    # WARNING: Only use this in development or trusted corporate networks
    import httpx
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Monkey patch httpx to disable SSL verification
    import ssl
    _original_create_default_context = ssl.create_default_context
    
    def _create_unverified_context(*args, **kwargs):
        context = _original_create_default_context(*args, **kwargs)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    # Initialize Ollama LLM (local model, GPU-accelerated)
    logger.info("Initializing Ollama LLM with qwen3:8b model (GPU-accelerated)...")
    llm = ChatOllama(
        model="qwen3:8b",  # Using Qwen 3 8B model with GPU acceleration
        temperature=0.1,
        base_url="http://localhost:11434"  # Default Ollama URL
    )
    logger.info("LLM initialized successfully")
    
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

def run_incident_commander(incident_data: dict):
    """Execute the Autonomous Incident Commander
    
    Args:
        incident_data: Comprehensive incident data including:
        - incident_id, timestamp_utc, environment, region
        - service: {name, version, instance_count}
        - trigger: {type, source, severity, alert_name, firing_duration_seconds}
        - metrics_snapshot: {...}
        - log_signals: {...}
        - deployment_context: {...}
        - customer_impact: {...}
        - correlation_ids: {...}
        - log_file_path: (optional) path to log file for analysis
    """
    logger.info("#"*70)
    logger.info("AUTONOMOUS INCIDENT COMMANDER STARTING")
    logger.info("#"*70)
    logger.info(f"Incident ID: {incident_data.get('incident_id')}")
    logger.info(f"Environment: {incident_data.get('environment')}")
    logger.info(f"Service: {incident_data.get('service', {}).get('name')}")
    
    # Create the graph
    logger.info("Creating incident commander graph...")
    app = create_incident_commander_graph()
    logger.info("Graph created successfully")
    
    # Initialize state with comprehensive incident data
    initial_state = {
        "incident_id": incident_data.get("incident_id"),
        "timestamp_utc": incident_data.get("timestamp_utc"),
        "environment": incident_data.get("environment"),
        "region": incident_data.get("region"),
        "service": incident_data.get("service", {}),
        "trigger": incident_data.get("trigger", {}),
        "metrics_snapshot": incident_data.get("metrics_snapshot", {}),
        "log_signals": incident_data.get("log_signals", {}),
        "deployment_context": incident_data.get("deployment_context", {}),
        "customer_impact": incident_data.get("customer_impact", {}),
        "correlation_ids": incident_data.get("correlation_ids", {}),
        "log_file_path": incident_data.get("log_file_path", ""),  # Empty string if not provided
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
    logger.info("Invoking graph with initial state...")
    final_state = app.invoke(initial_state)
    logger.info("Graph execution complete")
    logger.info("#"*70)
    logger.info("INCIDENT COMMANDER FINISHED")
    logger.info("#"*70)
    
    return final_state


if __name__ == "__main__":
    # Example comprehensive incident in the expected format
    example_incident = {
        "incident_id": "inc-2026-02-06-113742",
        "timestamp_utc": "2026-02-06T11:37:42.391Z",
        "environment": "production",
        "region": "ap-southeast-1",
        "service": {
            "name": "checkout-service",
            "version": "v2.18.4",
            "instance_count": 24
        },
        "trigger": {
            "type": "alert",
            "source": "prometheus",
            "severity": "critical",
            "alert_name": "High_P99_Latency",
            "firing_duration_seconds": 312
        },
        "metrics_snapshot": {
            "p99_latency_ms": 1860,
            "baseline_p99_latency_ms": 420,
            "cpu_utilization_pct": 91.4,
            "memory_utilization_pct": 88.9,
            "error_rate_pct": 3.7
        },
        "log_signals": {
            "error_count_last_5min": 1243,
            "dominant_exception": "java.lang.OutOfMemoryError: GC overhead limit exceeded",
            "sample_stack_trace_hash": "a9f3c2d7",
            "affected_endpoints": [
                "/checkout/confirm",
                "/checkout/apply-coupon"
            ]
        },
        "deployment_context": {
            "last_deploy_id": "deploy-74219",
            "last_deploy_timestamp_utc": "2026-02-06T11:12:08.000Z",
            "time_since_last_deploy_minutes": 25,
            "changed_components": [
                "pricing-engine",
                "promotion-rules"
            ],
            "config_changes": [
                {
                    "key": "promo.cache.ttl",
                    "old_value": "300s",
                    "new_value": "0s"
                }
            ]
        },
        "customer_impact": {
            "estimated_affected_requests_pct": 18.6,
            "failed_transactions_last_10min": 742,
            "revenue_impact_usd_per_min": 4200
        },
        "correlation_ids": {
            "trace_id_sample": "4f3c9b2a8d1e",
            "request_id_sample": "req-882193ab"
        },
        "log_file_path": "sample_logs.json"  # Add log file for analysis
    }

    
    # Run the incident commander with the comprehensive incident
    result = run_incident_commander(example_incident)
    
    print("\n" + "="*70)
    print("  EXECUTION COMPLETE")
    print("="*70)



