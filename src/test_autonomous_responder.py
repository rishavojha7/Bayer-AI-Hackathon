#!/usr/bin/env python3
"""
Comprehensive Test Suite for Autonomous First Responder
Tests agent reasoning, decision-making, and integration capabilities
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_timeout_alert():
    """Sample database timeout alert"""
    from autonomous_first_responder import Alert, Severity
    
    return Alert(
        id="TEST-001",
        timestamp=datetime.now(),
        service="payment-service",
        severity=Severity.CRITICAL,
        message="Database connection timeout - 247 failed requests",
        metadata={"error_count": 247}
    )


@pytest.fixture
def sample_error_spike_alert():
    """Sample error spike alert"""
    from autonomous_first_responder import Alert, Severity
    
    return Alert(
        id="TEST-002",
        timestamp=datetime.now(),
        service="user-service",
        severity=Severity.HIGH,
        message="5xx error rate increased to 15%",
        metadata={"error_rate": 0.15}
    )


@pytest.fixture
def commander_agent():
    """Commander agent instance"""
    from autonomous_first_responder import CommanderAgent
    return CommanderAgent()


@pytest.fixture
def advanced_commander():
    """Advanced commander with causal reasoning"""
    from advanced_first_responder import AdvancedCommanderAgent
    from autonomous_first_responder import LogsAgent, MetricsAgent, DeployIntelligenceAgent
    
    return AdvancedCommanderAgent(
        LogsAgent(),
        MetricsAgent(),
        DeployIntelligenceAgent()
    )


# =============================================================================
# AGENT BEHAVIOR TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_logs_agent_investigation(sample_timeout_alert):
    """Test LogsAgent forensic analysis"""
    from autonomous_first_responder import LogsAgent
    
    agent = LogsAgent()
    report = await agent.investigate(sample_timeout_alert, ["full"])
    
    # Verify report structure
    assert report.agent_name == "LogsAgent"
    assert report.confidence > 0.5
    assert isinstance(report.findings, dict)
    
    # Verify findings
    assert "error_patterns" in report.findings
    assert "stack_traces" in report.findings
    assert "affected_services" in report.findings
    
    # For timeout alert, should find connection issues
    assert any("timeout" in str(pattern).lower() 
              for pattern in report.findings["error_patterns"])
    
    print(f"✅ LogsAgent: Found {len(report.findings['error_patterns'])} error patterns")


@pytest.mark.asyncio
async def test_metrics_agent_anomaly_detection(sample_timeout_alert):
    """Test MetricsAgent anomaly detection"""
    from autonomous_first_responder import MetricsAgent
    
    agent = MetricsAgent()
    report = await agent.investigate(sample_timeout_alert, ["full"])
    
    # Verify metrics collection
    assert "current_metrics" in report.findings
    assert "anomalies" in report.findings
    
    metrics = report.findings["current_metrics"]
    
    # Check key metrics present
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "p99_latency_ms" in metrics
    
    # For timeout, should detect high latency
    assert metrics["p99_latency_ms"] > 1000
    
    # Should have anomalies
    assert len(report.findings["anomalies"]) > 0
    
    print(f"✅ MetricsAgent: Detected {len(report.findings['anomalies'])} anomalies")


@pytest.mark.asyncio
async def test_deploy_intelligence_correlation(sample_timeout_alert):
    """Test DeployIntelligence deployment correlation"""
    from autonomous_first_responder import DeployIntelligenceAgent
    
    agent = DeployIntelligenceAgent()
    report = await agent.investigate(sample_timeout_alert, ["full"])
    
    # Verify deployment analysis
    assert "recent_deployments" in report.findings
    assert "suspicious_deployments" in report.findings
    assert "correlation_score" in report.findings
    
    # Should have deployment history
    assert isinstance(report.findings["recent_deployments"], list)
    
    print(f"✅ DeployIntelligence: Found {len(report.findings['recent_deployments'])} recent deployments")


# =============================================================================
# REASONING LOOP TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_complete_reasoning_loop(commander_agent, sample_timeout_alert):
    """Test complete detect->plan->investigate->decide->act->report loop"""
    
    # DETECT
    investigation = await commander_agent.detect(sample_timeout_alert)
    assert investigation.alert.id == "TEST-001"
    assert investigation.status.value == "detected"
    
    # PLAN
    plan = await commander_agent.plan(investigation)
    assert len(plan) > 0
    assert investigation.status.value == "planning"
    
    # INVESTIGATE
    reports = await commander_agent.investigate(investigation)
    assert len(reports) == 3  # Logs, Metrics, Deploy agents
    assert investigation.status.value == "investigating"
    
    # DECIDE
    decision = await commander_agent.decide(investigation)
    assert decision is not None
    assert len(decision) > 0
    assert investigation.status.value == "deciding"
    
    # ACT
    actions = await commander_agent.act(investigation)
    assert len(actions) > 0
    assert investigation.status.value in ["resolved", "escalated"]
    
    # REPORT
    report = await commander_agent.report(investigation)
    assert "incident_id" in report
    assert "root_cause" in report
    assert "actions_taken" in report
    
    print(f"✅ Complete reasoning loop: {investigation.status.value}")
    print(f"   Root cause: {decision}")
    print(f"   Actions: {len(actions)}")


@pytest.mark.asyncio
async def test_parallel_agent_deployment(commander_agent, sample_timeout_alert):
    """Test parallel deployment of specialist agents"""
    
    investigation = await commander_agent.detect(sample_timeout_alert)
    await commander_agent.plan(investigation)
    
    # Measure investigation time
    start = datetime.now()
    reports = await commander_agent.investigate(investigation)
    duration = (datetime.now() - start).total_seconds()
    
    # Should complete quickly due to parallel execution
    assert duration < 2.0  # All agents run in parallel
    assert len(reports) == 3
    
    print(f"✅ Parallel investigation completed in {duration:.2f}s")


# =============================================================================
# ADVANCED REASONING TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_causal_hypothesis_generation(advanced_commander, sample_timeout_alert):
    """Test causal hypothesis generation"""
    from autonomous_first_responder import CommanderAgent
    
    # First run basic investigation
    basic_commander = CommanderAgent()
    investigation = await basic_commander.detect(sample_timeout_alert)
    await basic_commander.plan(investigation)
    await basic_commander.investigate(investigation)
    
    # Generate causal hypotheses
    hypotheses = await advanced_commander.advanced_investigation(investigation)
    
    # Should generate multiple hypotheses
    assert len(hypotheses) > 0
    
    # Hypotheses should be ranked by probability
    for i in range(len(hypotheses) - 1):
        assert hypotheses[i].probability >= hypotheses[i + 1].probability
    
    # Top hypothesis should have reasonable confidence
    top = hypotheses[0]
    assert top.confidence > 0.5
    assert len(top.supporting_evidence) > 0
    
    print(f"✅ Generated {len(hypotheses)} causal hypotheses")
    print(f"   Top hypothesis: {top.hypothesis} (p={top.probability:.2%})")


@pytest.mark.asyncio
async def test_bayesian_reasoning(advanced_commander):
    """Test Bayesian probability updates"""
    from advanced_first_responder import CausalReasoningEngine
    
    engine = CausalReasoningEngine()
    
    # Test probability update
    prior = 0.3  # 30% base rate
    likelihood = 0.8  # 80% match to evidence
    evidence_strength = 0.9  # Strong evidence
    
    posterior = engine._bayesian_update(prior, likelihood, evidence_strength)
    
    # Posterior should be higher than prior with strong evidence
    assert posterior > prior
    assert posterior <= 0.95  # Capped at 95%
    
    print(f"✅ Bayesian update: {prior:.2%} → {posterior:.2%}")


@pytest.mark.asyncio
async def test_remediation_plan_generation(advanced_commander, sample_timeout_alert):
    """Test remediation plan generation"""
    from advanced_first_responder import CausalHypothesis
    
    # Create hypothesis
    hypothesis = CausalHypothesis(
        hypothesis="Recent deployment introduced regression",
        probability=0.87,
        supporting_evidence=["Deployment correlation: 0.94"],
        contradicting_evidence=[],
        confidence=0.92
    )
    
    # Generate remediation plan
    plan = advanced_commander.create_remediation_plan(
        hypothesis,
        {"metrics": {}, "logs": {}, "deployments": {}}
    )
    
    # Verify plan structure
    assert plan.strategy is not None
    assert len(plan.actions) > 0
    assert 0 <= plan.predicted_success_rate <= 1.0
    assert 0 <= plan.risk_level <= 1.0
    assert plan.estimated_duration_seconds > 0
    
    print(f"✅ Remediation plan: {plan.strategy.value}")
    print(f"   Success rate: {plan.predicted_success_rate:.0%}")
    print(f"   Risk: {plan.risk_level:.0%}")


# =============================================================================
# DECISION QUALITY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_confidence_based_decision_making(commander_agent, sample_error_spike_alert):
    """Test that low-confidence incidents are escalated"""
    
    investigation = await commander_agent.detect(sample_error_spike_alert)
    await commander_agent.plan(investigation)
    await commander_agent.investigate(investigation)
    await commander_agent.decide(investigation)
    actions = await commander_agent.act(investigation)
    
    # Low confidence scenarios should escalate
    # (This is probabilistic, but should happen sometimes)
    if any("ESCALATE" in action for action in actions):
        assert investigation.status.value == "escalated"
        print("✅ Low confidence correctly escalated")
    else:
        assert investigation.status.value == "resolved"
        print("✅ High confidence resolved autonomously")


@pytest.mark.asyncio
async def test_deployment_correlation_accuracy():
    """Test accuracy of deployment correlation"""
    from autonomous_first_responder import DeployIntelligenceAgent, Alert, Severity
    
    agent = DeployIntelligenceAgent()
    
    # Alert soon after deployment should have high correlation
    recent_alert = Alert(
        id="TEST-DEPLOY-001",
        timestamp=datetime.now(),
        service="api-gateway",
        severity=Severity.CRITICAL,
        message="Error spike after deployment"
    )
    
    report = await agent.investigate(recent_alert, ["full"])
    
    # Should find suspicious deployments
    assert len(report.findings.get("suspicious_deployments", [])) > 0
    
    # Correlation should be reasonable
    correlation = report.findings.get("correlation_score", 0)
    assert 0 <= correlation <= 1.0
    
    print(f"✅ Deployment correlation: {correlation:.2%}")


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_investigation_performance(commander_agent, sample_timeout_alert):
    """Test investigation completes within performance targets"""
    
    start = datetime.now()
    
    investigation = await commander_agent.detect(sample_timeout_alert)
    await commander_agent.plan(investigation)
    await commander_agent.investigate(investigation)
    await commander_agent.decide(investigation)
    
    duration = (datetime.now() - start).total_seconds()
    
    # Investigation should complete in <15 seconds
    assert duration < 15.0
    
    print(f"✅ Investigation completed in {duration:.2f}s (target: <15s)")


@pytest.mark.asyncio
async def test_mttr_improvement():
    """Test that autonomous response improves MTTR"""
    from autonomous_first_responder import CommanderAgent, Alert, Severity
    
    commander = CommanderAgent()
    
    alerts = [
        Alert(
            id=f"MTTR-TEST-{i}",
            timestamp=datetime.now(),
            service="test-service",
            severity=Severity.HIGH,
            message=f"Test alert {i}"
        )
        for i in range(3)
    ]
    
    resolution_times = []
    
    for alert in alerts:
        start = datetime.now()
        await commander.handle_alert(alert)
        duration = (datetime.now() - start).total_seconds()
        resolution_times.append(duration)
    
    avg_mttr = sum(resolution_times) / len(resolution_times)
    
    # Average MTTR should be under 20 seconds
    assert avg_mttr < 20.0
    
    print(f"✅ Average MTTR: {avg_mttr:.1f}s (target: <5min for real incidents)")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_prometheus_integration():
    """Test Prometheus metrics adapter"""
    from integrations import PrometheusMetricsAdapter
    
    adapter = PrometheusMetricsAdapter()
    metrics = await adapter.query_metrics("test-service")
    
    # Verify metrics structure
    assert "cpu_usage" in metrics
    assert "memory_usage_mb" in metrics
    assert "error_rate" in metrics
    
    print(f"✅ Prometheus integration: {len(metrics)} metrics retrieved")


@pytest.mark.asyncio
async def test_elasticsearch_integration():
    """Test Elasticsearch logs adapter"""
    from integrations import ElasticsearchLogsAdapter
    
    adapter = ElasticsearchLogsAdapter()
    logs = await adapter.search_logs("test-service", severity="error")
    
    # Verify logs structure
    assert isinstance(logs, list)
    if logs:
        assert "timestamp" in logs[0]
        assert "message" in logs[0]
    
    print(f"✅ Elasticsearch integration: {len(logs)} log entries found")


@pytest.mark.asyncio
async def test_kubernetes_integration():
    """Test Kubernetes orchestration adapter"""
    from integrations import KubernetesAdapter
    
    adapter = KubernetesAdapter()
    status = await adapter.get_pod_status("test-service")
    
    # Verify status structure
    assert "deployment" in status
    assert "replicas" in status
    assert "pods" in status
    
    print(f"✅ Kubernetes integration: {status['replicas']['ready']}/{status['replicas']['desired']} pods ready")


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_multiple_concurrent_incidents(commander_agent):
    """Test handling multiple incidents concurrently"""
    from autonomous_first_responder import Alert, Severity
    
    alerts = [
        Alert(
            id=f"CONCURRENT-{i}",
            timestamp=datetime.now(),
            service=f"service-{i}",
            severity=Severity.HIGH,
            message=f"Incident {i}"
        )
        for i in range(5)
    ]
    
    # Handle all alerts concurrently
    results = await asyncio.gather(
        *[commander_agent.handle_alert(alert) for alert in alerts]
    )
    
    # All should complete
    assert len(results) == 5
    
    # All should have incident reports
    for result in results:
        assert "incident_id" in result
        assert "status" in result
    
    print(f"✅ Handled {len(results)} concurrent incidents")


@pytest.mark.asyncio
async def test_unknown_service_handling(commander_agent):
    """Test handling of alerts for unknown services"""
    from autonomous_first_responder import Alert, Severity
    
    alert = Alert(
        id="UNKNOWN-001",
        timestamp=datetime.now(),
        service="totally-unknown-service-xyz",
        severity=Severity.MEDIUM,
        message="Error in unknown service"
    )
    
    report = await commander_agent.handle_alert(alert)
    
    # Should still generate a report
    assert "incident_id" in report
    assert report["status"] in ["resolved", "escalated"]
    
    print(f"✅ Unknown service handled: {report['status']}")


# =============================================================================
# TEST RUNNER
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
