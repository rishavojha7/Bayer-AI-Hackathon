"""Mock LLM for testing when API access is blocked"""
import json
from typing import Any, List
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import Generation, LLMResult


class MockGeminiLLM:
    """Mock LLM that simulates Gemini responses for testing"""
    
    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Generate mock responses based on the prompt context"""
        
        # Get the last message content
        if isinstance(messages, list):
            last_msg = str(messages[-1].content) if messages else ""
        else:
            last_msg = str(messages)
        
        # Generate contextual mock responses
        if "investigation plan" in last_msg.lower():
            response = json.dumps([
                "Analyze latency spike correlation with recent deployment",
                "Investigate OutOfMemoryError and GC overhead issues",
                "Examine cache configuration change impact (promo.cache.ttl: 300s -> 0s)",
                "Assess pricing-engine and promotion-rules changes",
                "Review memory utilization patterns and heap allocation",
                "Correlate error spike timing with deployment timestamp"
            ])
        
        elif "metrics" in last_msg.lower() and "analyze" in last_msg.lower():
            response = json.dumps({
                "latency_spike": True,
                "latency_p99": 1860,
                "baseline_p99": 420,
                "latency_increase_pct": 343,
                "cpu_utilization_high": True,
                "cpu_value": 91.4,
                "memory_utilization_high": True,
                "memory_value": 88.9,
                "error_rate_elevated": True,
                "error_rate_pct": 3.7,
                "analysis": "Severe performance degradation: P99 latency increased 343% above baseline. High CPU and memory utilization coupled with elevated error rate indicates resource exhaustion.",
                "anomalies_detected": [
                    "P99 latency 343% above baseline (1860ms vs 420ms)",
                    "CPU utilization at 91.4% - critically high",
                    "Memory utilization at 88.9% - near capacity",
                    "Error rate at 3.7% - significantly elevated"
                ],
                "critical_issues": [
                    "Memory pressure evident from high utilization",
                    "Performance degradation correlates with recent deployment",
                    "Resource exhaustion pattern detected"
                ]
            })
        
        elif "logs" in last_msg.lower() and "forensics" in last_msg.lower():
            response = json.dumps({
                "error_count": 1243,
                "dominant_exception": "java.lang.OutOfMemoryError: GC overhead limit exceeded",
                "exception_category": "memory",
                "stack_trace_analyzed": True,
                "affected_endpoints": ["/checkout/confirm", "/checkout/apply-coupon"],
                "affected_endpoint_count": 2,
                "error_rate_trend": "increasing",
                "pattern_analysis": "OutOfMemoryError indicates JVM heap exhaustion. GC overhead limit exceeded suggests garbage collector is consuming excessive CPU trying to free memory. This pattern started after the recent deployment that changed cache TTL to 0s, likely causing excessive object creation.",
                "suspected_causes": [
                    "Cache TTL set to 0s causing no caching and excessive object allocation",
                    "Promotion-rules changes may have memory leak",
                    "Pricing-engine update possibly creating long-lived objects"
                ],
                "oom_detected": True
            })
        
        elif "deployment" in last_msg.lower() and "correlate" in last_msg.lower():
            response = json.dumps({
                "deployment_related": True,
                "deployment_id": "deploy-74219",
                "deployment_time": "2026-02-06T11:12:08.000Z",
                "time_since_deploy_minutes": 25,
                "changed_components": ["pricing-engine", "promotion-rules"],
                "config_changes_detected": True,
                "risky_config_changes": ["promo.cache.ttl"],
                "rollback_recommended": True,
                "correlation_analysis": "CRITICAL: Configuration change detected - promo.cache.ttl changed from 300s to 0s just 25 minutes before incident. This disables caching entirely, causing massive memory allocation for every request. Combined with changes to pricing-engine and promotion-rules, this creates a perfect storm for memory exhaustion.",
                "risk_assessment": "critical"
            })
        
        elif "root cause" in last_msg.lower():
            response = json.dumps({
                "root_cause": "Configuration error in deploy-74219: promo.cache.ttl set to 0s disabled promotional caching, causing excessive memory allocation. Every checkout request now creates new promotion calculation objects instead of reusing cached results. Combined with changes to promotion-rules, this triggered rapid memory exhaustion (88.9% utilization), GC thrashing (91.4% CPU), and OutOfMemoryError cascade affecting /checkout/confirm and /checkout/apply-coupon endpoints.",
                "confidence": 0.95
            })
        
        elif "remediation" in last_msg.lower():
            response = json.dumps([
                "IMMEDIATE: Rollback deploy-74219 to restore promo.cache.ttl=300s",
                "IMMEDIATE: Restart checkout-service instances to clear memory",
                "Monitor memory utilization and P99 latency for stabilization",
                "Review promotion-rules and pricing-engine changes before redeployment",
                "Implement memory profiling to identify any additional leaks",
                "Add alerting for cache configuration changes",
                "Conduct post-incident review of deployment validation process"
            ])
        
        else:
            response = json.dumps({
                "result": "Mock LLM response",
                "note": "This is a simulated response for testing"
            })
        
        return AIMessage(content=response)


def create_mock_llm():
    """Create a mock LLM instance"""
    return MockGeminiLLM()
