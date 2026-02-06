#!/usr/bin/env python3
"""
Advanced Autonomous First Responder
Enhanced multi-agent reasoning with causal inference and learning capabilities

Key Enhancements:
- Causal reasoning: Builds dependency graphs to understand failure propagation
- Confidence scoring: Bayesian inference for decision quality
- Learning from incidents: Pattern recognition for faster future response
- Action simulation: Predicts outcome before executing remediation
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
import math


class RemediationStrategy(Enum):
    """Available remediation strategies"""
    ROLLBACK = "rollback"
    SCALE_UP = "scale_up"
    CIRCUIT_BREAK = "circuit_break"
    RESTART = "restart"
    CONFIG_REVERT = "config_revert"
    TRAFFIC_SHED = "traffic_shed"
    ESCALATE = "escalate"


@dataclass
class ServiceDependency:
    """Service dependency relationship"""
    service: str
    depends_on: List[str]
    criticality: float  # 0.0 to 1.0


@dataclass
class CausalHypothesis:
    """Hypothesis about root cause"""
    hypothesis: str
    probability: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    confidence: float


@dataclass
class RemediationPlan:
    """Structured remediation plan with predicted outcomes"""
    strategy: RemediationStrategy
    actions: List[Dict[str, Any]]
    predicted_success_rate: float
    risk_level: float
    estimated_duration_seconds: int
    rollback_plan: Optional[List[str]] = None


class CausalReasoningEngine:
    """Advanced reasoning engine for root cause analysis"""
    
    def __init__(self):
        # Service dependency graph
        self.dependencies = {
            "api-gateway": ServiceDependency("api-gateway", ["user-service", "payment-service"], 0.9),
            "user-service": ServiceDependency("user-service", ["database", "cache"], 0.8),
            "payment-service": ServiceDependency("payment-service", ["database", "payment-processor"], 0.9),
            "database": ServiceDependency("database", [], 1.0),
            "cache": ServiceDependency("cache", [], 0.6),
            "payment-processor": ServiceDependency("payment-processor", [], 0.8),
        }
        
        # Historical incident patterns
        self.incident_patterns = []
    
    def build_failure_propagation_tree(self, failed_service: str, 
                                      findings: Dict[str, Any]) -> Dict[str, Any]:
        """Build tree showing how failure could have propagated"""
        tree = {
            "root_service": failed_service,
            "propagation_paths": [],
            "blast_radius": set()
        }
        
        # Find services that depend on the failed service
        dependent_services = [
            name for name, dep in self.dependencies.items()
            if failed_service in dep.depends_on
        ]
        
        tree["propagation_paths"] = [{
            "from": failed_service,
            "to": dependent,
            "impact_probability": self.dependencies[dependent].criticality
        } for dependent in dependent_services]
        
        tree["blast_radius"] = set([failed_service] + dependent_services)
        
        return tree
    
    def generate_causal_hypotheses(self, 
                                  alert: Any,
                                  logs_findings: Dict[str, Any],
                                  metrics_findings: Dict[str, Any],
                                  deploy_findings: Dict[str, Any]) -> List[CausalHypothesis]:
        """Generate and rank causal hypotheses using Bayesian reasoning"""
        
        hypotheses = []
        
        # Hypothesis 1: Recent deployment caused regression
        if deploy_findings.get("correlation_score", 0) > 0.6:
            evidence_for = [
                f"Deployment correlation: {deploy_findings['correlation_score']:.2f}",
                f"{len(deploy_findings.get('suspicious_deployments', []))} suspicious deployments found"
            ]
            evidence_against = []
            
            if logs_findings.get("error_patterns"):
                if "connection" in str(logs_findings["error_patterns"]).lower():
                    evidence_against.append("Error patterns suggest infrastructure issue")
            
            prior_prob = 0.4  # Base rate for deployment-caused issues
            likelihood = deploy_findings["correlation_score"]
            
            # Bayesian update
            posterior = self._bayesian_update(prior_prob, likelihood, 0.7)
            
            hypotheses.append(CausalHypothesis(
                hypothesis="Recent deployment introduced regression",
                probability=posterior,
                supporting_evidence=evidence_for,
                contradicting_evidence=evidence_against,
                confidence=min(0.95, deploy_findings["correlation_score"] + 0.1)
            ))
        
        # Hypothesis 2: Resource exhaustion
        if metrics_findings.get("resource_exhaustion"):
            resources = metrics_findings["resource_exhaustion"]
            evidence_for = [
                f"Resource exhaustion detected: {', '.join(resources)}",
                f"Anomalies: {len(metrics_findings.get('anomalies', []))}"
            ]
            
            # Check if gradual degradation
            trend = metrics_findings.get("trend_analysis", {})
            if trend.get("rate_of_change") == "rapid":
                evidence_for.append("Rapid degradation pattern consistent with resource leak")
            
            evidence_against = []
            if deploy_findings.get("suspicious_deployments"):
                evidence_against.append("Timing coincides with deployment")
            
            prior_prob = 0.3
            likelihood = 0.8 if len(resources) > 1 else 0.6
            posterior = self._bayesian_update(prior_prob, likelihood, 0.8)
            
            hypotheses.append(CausalHypothesis(
                hypothesis=f"Resource exhaustion: {resources[0]}",
                probability=posterior,
                supporting_evidence=evidence_for,
                contradicting_evidence=evidence_against,
                confidence=0.85
            ))
        
        # Hypothesis 3: Cascading failure from dependency
        if len(logs_findings.get("affected_services", [])) > 1:
            propagation = self.build_failure_propagation_tree(
                alert.service, 
                {"logs": logs_findings, "metrics": metrics_findings}
            )
            
            evidence_for = [
                f"Multiple services affected: {logs_findings['affected_services']}",
                f"Blast radius: {len(propagation['blast_radius'])} services"
            ]
            
            if logs_findings.get("error_correlation", {}).get("correlation_coefficient", 0) > 0.8:
                evidence_for.append("High error correlation across services")
            
            prior_prob = 0.25
            likelihood = len(propagation["blast_radius"]) / 10.0  # Normalize
            posterior = self._bayesian_update(prior_prob, likelihood, 0.6)
            
            hypotheses.append(CausalHypothesis(
                hypothesis="Cascading failure from upstream dependency",
                probability=posterior,
                supporting_evidence=evidence_for,
                contradicting_evidence=[],
                confidence=0.75
            ))
        
        # Hypothesis 4: Application bug
        if logs_findings.get("stack_traces"):
            evidence_for = [
                f"Stack traces found: {len(logs_findings['stack_traces'])}",
                f"Error patterns: {logs_findings['error_patterns'][:2]}"
            ]
            
            evidence_against = []
            if metrics_findings.get("resource_exhaustion"):
                evidence_against.append("Resource exhaustion also present")
            
            prior_prob = 0.35
            likelihood = 0.7
            posterior = self._bayesian_update(prior_prob, likelihood, 0.75)
            
            hypotheses.append(CausalHypothesis(
                hypothesis="Application code defect",
                probability=posterior,
                supporting_evidence=evidence_for,
                contradicting_evidence=evidence_against,
                confidence=0.80
            ))
        
        # Sort by probability
        hypotheses.sort(key=lambda h: h.probability, reverse=True)
        
        return hypotheses
    
    def _bayesian_update(self, prior: float, likelihood: float, 
                        evidence_strength: float) -> float:
        """Bayesian probability update"""
        # P(H|E) = P(E|H) * P(H) / P(E)
        # Simplified: weight likelihood by evidence strength
        posterior = (likelihood * evidence_strength * prior) / \
                   (likelihood * evidence_strength * prior + (1 - prior))
        return min(0.95, posterior)  # Cap at 95%


class AdvancedCommanderAgent:
    """Enhanced commander with causal reasoning and learning"""
    
    def __init__(self, logs_agent, metrics_agent, deploy_agent):
        self.name = "AdvancedCommander"
        self.logs_agent = logs_agent
        self.metrics_agent = metrics_agent
        self.deploy_agent = deploy_agent
        self.reasoning_engine = CausalReasoningEngine()
        self.incident_history = []
    
    async def advanced_investigation(self, investigation: Any) -> List[CausalHypothesis]:
        """Enhanced investigation with causal reasoning"""
        
        print(f"[{self.name}] 🧠 Running advanced causal analysis...\n")
        
        # Get agent reports
        logs_report = investigation.findings["agent_reports"][0]
        metrics_report = investigation.findings["agent_reports"][1]
        deploy_report = investigation.findings["agent_reports"][2]
        
        # Generate causal hypotheses
        hypotheses = self.reasoning_engine.generate_causal_hypotheses(
            investigation.alert,
            logs_report.findings,
            metrics_report.findings,
            deploy_report.findings
        )
        
        print(f"[{self.name}] 🎯 CAUSAL HYPOTHESES (Ranked by probability):\n")
        for i, hyp in enumerate(hypotheses, 1):
            print(f"  {i}. {hyp.hypothesis}")
            print(f"     Probability: {hyp.probability:.2%} | Confidence: {hyp.confidence:.2%}")
            print(f"     Supporting: {len(hyp.supporting_evidence)} | Contradicting: {len(hyp.contradicting_evidence)}")
            if hyp.supporting_evidence:
                for evidence in hyp.supporting_evidence[:2]:
                    print(f"       + {evidence}")
            print()
        
        return hypotheses
    
    def create_remediation_plan(self, 
                               primary_hypothesis: CausalHypothesis,
                               findings: Dict[str, Any]) -> RemediationPlan:
        """Create detailed remediation plan with predicted outcomes"""
        
        hypothesis = primary_hypothesis.hypothesis.lower()
        
        if "deployment" in hypothesis or "regression" in hypothesis:
            return RemediationPlan(
                strategy=RemediationStrategy.ROLLBACK,
                actions=[
                    {"action": "identify_previous_stable_version", "duration_sec": 10},
                    {"action": "execute_rollback", "duration_sec": 120},
                    {"action": "verify_service_health", "duration_sec": 60}
                ],
                predicted_success_rate=0.85,
                risk_level=0.2,
                estimated_duration_seconds=190,
                rollback_plan=["Redeploy current version if rollback fails"]
            )
        
        elif "resource exhaustion" in hypothesis:
            resources = findings["metrics"].get("resource_exhaustion", ["memory"])
            return RemediationPlan(
                strategy=RemediationStrategy.SCALE_UP,
                actions=[
                    {"action": f"scale_{resources[0]}", "target": "2x current", "duration_sec": 90},
                    {"action": "monitor_resource_utilization", "duration_sec": 120},
                    {"action": "verify_error_rate_decrease", "duration_sec": 60}
                ],
                predicted_success_rate=0.75,
                risk_level=0.3,
                estimated_duration_seconds=270,
                rollback_plan=["Scale back if no improvement after 5 minutes"]
            )
        
        elif "cascading" in hypothesis or "dependency" in hypothesis:
            return RemediationPlan(
                strategy=RemediationStrategy.CIRCUIT_BREAK,
                actions=[
                    {"action": "activate_circuit_breaker", "target": "failing_dependency", "duration_sec": 5},
                    {"action": "enable_fallback_mechanism", "duration_sec": 30},
                    {"action": "monitor_error_recovery", "duration_sec": 120}
                ],
                predicted_success_rate=0.70,
                risk_level=0.4,
                estimated_duration_seconds=155,
                rollback_plan=["Deactivate circuit breaker", "Restore normal traffic flow"]
            )
        
        else:  # Application bug or unknown
            return RemediationPlan(
                strategy=RemediationStrategy.RESTART,
                actions=[
                    {"action": "rolling_restart", "batch_size": "25%", "duration_sec": 180},
                    {"action": "monitor_instance_health", "duration_sec": 90},
                    {"action": "verify_error_resolution", "duration_sec": 60}
                ],
                predicted_success_rate=0.60,
                risk_level=0.5,
                estimated_duration_seconds=330,
                rollback_plan=["Stop restart", "Escalate to engineering team"]
            )
    
    async def execute_remediation_with_monitoring(self, 
                                                  plan: RemediationPlan,
                                                  investigation: Any) -> Dict[str, Any]:
        """Execute remediation with continuous monitoring and rollback capability"""
        
        print(f"\n[{self.name}] 🎬 EXECUTING REMEDIATION PLAN")
        print(f"  Strategy: {plan.strategy.value}")
        print(f"  Predicted Success: {plan.predicted_success_rate:.0%}")
        print(f"  Risk Level: {plan.risk_level:.0%}")
        print(f"  Estimated Duration: {plan.estimated_duration_seconds}s\n")
        
        execution_result = {
            "plan": plan.strategy.value,
            "steps_completed": [],
            "success": False,
            "actual_duration": 0,
            "rollback_triggered": False
        }
        
        start_time = datetime.now()
        
        for i, action in enumerate(plan.actions, 1):
            action_name = action["action"]
            print(f"  [{i}/{len(plan.actions)}] Executing: {action_name}")
            
            # Simulate action execution
            duration = action.get("duration_sec", 30)
            await asyncio.sleep(min(0.5, duration / 100))  # Scaled for demo
            
            # Simulate success/failure with probability
            success = True  # In real system, check actual metrics
            
            if success:
                print(f"       ✅ Completed in {duration}s")
                execution_result["steps_completed"].append(action_name)
            else:
                print(f"       ❌ Failed - initiating rollback")
                execution_result["rollback_triggered"] = True
                
                # Execute rollback plan
                if plan.rollback_plan:
                    print(f"\n  🔄 ROLLBACK INITIATED")
                    for rollback_action in plan.rollback_plan:
                        print(f"     ↩️  {rollback_action}")
                        await asyncio.sleep(0.3)
                
                break
        
        execution_result["actual_duration"] = (datetime.now() - start_time).total_seconds()
        execution_result["success"] = len(execution_result["steps_completed"]) == len(plan.actions)
        
        if execution_result["success"]:
            print(f"\n  ✅ REMEDIATION SUCCESSFUL")
        else:
            print(f"\n  ⚠️  REMEDIATION PARTIAL - Escalating to human operator")
        
        print()
        
        return execution_result
    
    async def handle_alert_with_advanced_reasoning(self, alert: Any, 
                                                   investigation: Any) -> Dict[str, Any]:
        """Handle alert with advanced causal reasoning and planning"""
        
        # Generate causal hypotheses
        hypotheses = await self.advanced_investigation(investigation)
        
        # Select primary hypothesis (highest probability)
        primary_hypothesis = hypotheses[0] if hypotheses else None
        
        if not primary_hypothesis or primary_hypothesis.probability < 0.3:
            print(f"[{self.name}] ⚠️  Low confidence in root cause - ESCALATING\n")
            return {
                "decision": "ESCALATE - Insufficient confidence for autonomous remediation",
                "hypotheses": hypotheses,
                "confidence": primary_hypothesis.confidence if primary_hypothesis else 0.0
            }
        
        investigation.decision = primary_hypothesis.hypothesis
        
        print(f"[{self.name}] 💡 PRIMARY HYPOTHESIS: {primary_hypothesis.hypothesis}")
        print(f"  Confidence: {primary_hypothesis.confidence:.0%}\n")
        
        # Create remediation plan
        plan = self.create_remediation_plan(primary_hypothesis, investigation.findings)
        
        # Execute with monitoring
        execution_result = await self.execute_remediation_with_monitoring(plan, investigation)
        
        # Record incident for learning
        self.incident_history.append({
            "alert": alert,
            "hypothesis": primary_hypothesis.hypothesis,
            "remediation": plan.strategy.value,
            "success": execution_result["success"],
            "timestamp": datetime.now()
        })
        
        return {
            "decision": primary_hypothesis.hypothesis,
            "hypotheses": hypotheses,
            "remediation_plan": plan,
            "execution_result": execution_result,
            "confidence": primary_hypothesis.confidence
        }
    
    def generate_incident_insights(self) -> Dict[str, Any]:
        """Analyze historical incidents for patterns and learning"""
        
        if not self.incident_history:
            return {"insights": "Insufficient data"}
        
        total = len(self.incident_history)
        successful = sum(1 for inc in self.incident_history if inc["success"])
        
        # Most common root causes
        causes = {}
        for inc in self.incident_history:
            cause = inc["hypothesis"]
            causes[cause] = causes.get(cause, 0) + 1
        
        # Most effective strategies
        strategies = {}
        for inc in self.incident_history:
            if inc["success"]:
                strat = inc["remediation"]
                strategies[strat] = strategies.get(strat, 0) + 1
        
        return {
            "total_incidents": total,
            "success_rate": successful / total if total > 0 else 0,
            "common_root_causes": sorted(causes.items(), key=lambda x: x[1], reverse=True)[:3],
            "effective_strategies": sorted(strategies.items(), key=lambda x: x[1], reverse=True)[:3],
            "learning_status": "Active - improving response patterns"
        }


async def demonstrate_advanced_system():
    """Demonstrate advanced reasoning capabilities"""
    
    from autonomous_first_responder import (
        Alert, Severity, LogsAgent, MetricsAgent, 
        DeployIntelligenceAgent, CommanderAgent, Investigation, InvestigationStatus
    )
    
    # Create agents
    logs_agent = LogsAgent()
    metrics_agent = MetricsAgent()
    deploy_agent = DeployIntelligenceAgent()
    
    # Basic commander for initial setup
    basic_commander = CommanderAgent()
    
    # Advanced commander
    advanced_commander = AdvancedCommanderAgent(logs_agent, metrics_agent, deploy_agent)
    
    print("\n" + "="*80)
    print("ADVANCED AUTONOMOUS FIRST RESPONDER - CAUSAL REASONING DEMONSTRATION")
    print("="*80 + "\n")
    
    # Create complex scenario
    alert = Alert(
        id="INC-2024-ADV-001",
        timestamp=datetime.now(),
        service="api-gateway",
        severity=Severity.CRITICAL,
        message="Cascading failures detected - multiple services degraded",
        metadata={
            "affected_services": ["api-gateway", "user-service", "payment-service"],
            "error_spike": 0.34,
            "p99_latency": 8500
        }
    )
    
    # Run basic investigation
    investigation = await basic_commander.detect(alert)
    await basic_commander.plan(investigation)
    await basic_commander.investigate(investigation)
    
    # Run advanced reasoning
    result = await advanced_commander.handle_alert_with_advanced_reasoning(alert, investigation)
    
    # Generate final report
    print("\n" + "="*80)
    print("ADVANCED ANALYSIS REPORT")
    print("="*80)
    print(f"\nFinal Decision: {result['decision']}")
    print(f"Confidence: {result['confidence']:.0%}")
    
    if result.get('remediation_plan'):
        plan = result['remediation_plan']
        print(f"\nRemediation Strategy: {plan.strategy.value}")
        print(f"Predicted Success Rate: {plan.predicted_success_rate:.0%}")
        print(f"Risk Level: {plan.risk_level:.0%}")
    
    if result.get('execution_result'):
        exec_result = result['execution_result']
        print(f"\nExecution: {'SUCCESS' if exec_result['success'] else 'PARTIAL/ESCALATED'}")
        print(f"Steps Completed: {len(exec_result['steps_completed'])}")
    
    print("\n" + "="*80)
    print("\nAlternative Hypotheses Considered:")
    for i, hyp in enumerate(result['hypotheses'][:3], 1):
        print(f"{i}. {hyp.hypothesis} (p={hyp.probability:.2%})")
    
    # Show learning insights
    print("\n" + "="*80)
    print("SYSTEM LEARNING INSIGHTS")
    print("="*80)
    insights = advanced_commander.generate_incident_insights()
    print(json.dumps(insights, indent=2))
    print()


if __name__ == "__main__":
    asyncio.run(demonstrate_advanced_system())
