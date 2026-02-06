"""
Metrics Agent using LangGraph

This implements a simplified two-tool metrics monitoring system:
1. Analyzer: Checks metrics against thresholds and detects anomalies using LLM
2. Trend: Analyzes trends with sliding window of last 5 data points
"""

from collections import deque
from datetime import datetime
from typing import TypedDict, Dict, Any, Optional
import re
import json
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
import config
from metric_prompt import ANALYZER_PROMPT, TREND_PROMPT


# =============================================================================
# State Schema
# =============================================================================

class MetricsState(TypedDict):
    """State schema for the metrics agent graph"""
    raw_metrics: Dict[str, Any]
    timestamp: str
    analyzer_output: Optional[Dict[str, Any]]
    trend_output: Optional[Dict[str, Any]]
    combined_output: Optional[Dict[str, Any]]


# =============================================================================
# Shared LLM Instance
# =============================================================================

llm = ChatBedrock(model="meta.llama3-8b-instruct-v1:0", temperature=0)


# =============================================================================
# Tool 1: Analyzer
# =============================================================================

def analyzer_node(state: MetricsState) -> MetricsState:
    """
    Analyzer tool: Takes metrics + config, checks against thresholds
    and uses LLM to detect anomalies with structured output.
    
    Input: raw_metrics (dict)
    Output: analyzer_output (dict with anomaly detection results)
    """
    metrics = state["raw_metrics"]
    
    # Format thresholds for the prompt
    thresholds_str = json.dumps(config.THRESHOLDS, indent=2)
    metrics_str = json.dumps(metrics, indent=2)
    
    # Create prompt using the template
    prompt = ANALYZER_PROMPT.format(
        thresholds=thresholds_str,
        metrics=metrics_str
    )
    
    try:
        # Call LLM
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        result_text = response.content.strip()
        
        analyzer_output = json.loads(result_text)
        state["analyzer_output"] = analyzer_output
        
    except Exception as e:
        # If LLM call fails, provide fallback
        print(f"Analyzer error: {e}")
        state["analyzer_output"] = {
            "anomaly_detected": False,
            "message": f"Analysis error: {str(e)}"
        }
    
    return state


# =============================================================================
# Tool 2: Trend Analyzer (Stateful)
# =============================================================================

class TrendAnalyzer:
    """
    Stateful trend analyzer with sliding window of last 5 data points.
    """
    
    def __init__(self, window_size: int = 5):
        self.window = deque(maxlen=window_size)
    
    def analyze(self, state: MetricsState) -> MetricsState:
        """
        Analyze trends using current metrics and historical window.
        
        Input: raw_metrics
        Output: trend_output (dict with trend analysis)
        """
        current_metrics = state["raw_metrics"].copy()
        current_metrics["timestamp"] = state["timestamp"]
        
        # Add to sliding window
        self.window.append(current_metrics)
        
        # Prepare data for trend analysis
        current_str = json.dumps(current_metrics, indent=2)
        historical_str = json.dumps(list(self.window), indent=2)
        
        # Create prompt
        prompt = TREND_PROMPT.format(
            current_metrics=current_str,
            historical_metrics=historical_str
        )
        
        try:
            # Call LLM
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)
            result_text = response.content.strip()
            
            # Parse JSON response - handle multiple formats
            if "```json" in result_text:
                # Extract from markdown code block with json language
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                # Extract from plain markdown code block
                result_text = result_text.split("```")[1].split("```")[0].strip()
            else:
                # LLM returned plain text with JSON embedded - extract JSON between braces
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            trend_output = json.loads(result_text)
            state["trend_output"] = trend_output
            
        except Exception as e:
            # If LLM call fails, provide fallback
            print(f"Trend analysis error: {e}")
            state["trend_output"] = {
                "trends_detected": False,
                "message": f"Trend analysis error: {str(e)}"
            }
        
        return state


# Create singleton instance for stateful trend analysis
trend_analyzer = TrendAnalyzer()


def trend_node(state: MetricsState) -> MetricsState:
    """
    Wrapper node for the trend analyzer.
    Uses the stateful analyzer instance with sliding window.
    """
    return trend_analyzer.analyze(state)


# =============================================================================
# Combiner: Merge outputs from both tools
# =============================================================================

def combiner_node(state: MetricsState) -> MetricsState:
    """
    Combine outputs from Analyzer and Trend tools.
    
    Creates a unified output with both anomaly detection and trend analysis.
    """
    combined = {
        "timestamp": state["timestamp"],
        "metrics": state["raw_metrics"],
        "analyzer": state.get("analyzer_output", {}),
        "trends": state.get("trend_output", {}),
        "summary": _generate_summary(
            state.get("analyzer_output", {}),
            state.get("trend_output", {})
        )
    }
    
    state["combined_output"] = combined
    return state


def _generate_summary(analyzer_output: Dict, trend_output: Dict) -> Dict[str, Any]:
    """
    Generate a high-level summary combining both analyses.
    """
    summary = {
        "status": "normal",
        "alerts": [],
        "recommendations": []
    }
    
    # Check analyzer results
    if analyzer_output.get("anomaly_detected"):
        summary["status"] = "anomaly_detected"
        summary["alerts"].append(analyzer_output.get("hypothesis", "Anomaly detected"))
        if "recommendation" in analyzer_output:
            summary["recommendations"].append(analyzer_output["recommendation"])
    
    # Check trend results
    if trend_output.get("trends_detected"):
        concerning = trend_output.get("concerning_patterns", [])
        if concerning:
            if summary["status"] == "normal":
                summary["status"] = "warning"
            summary["alerts"].extend(concerning)
        
        if "early_warnings" in trend_output:
            summary["recommendations"].append(trend_output["early_warnings"])
    
    return summary


# =============================================================================
# LangGraph Workflow
# =============================================================================

def build_metrics_graph() -> StateGraph:
    """
    Build the LangGraph workflow for metrics monitoring.
    
    Flow:
    1. Analyzer → checks thresholds and detects anomalies
    2. Trend → analyzes trends over time
    3. Combiner → merges outputs
    4. END
    """
    workflow = StateGraph(MetricsState)
    
    # Add nodes
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("trend", trend_node)
    workflow.add_node("combiner", combiner_node)
    
    # Define edges
    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "trend")
    workflow.add_edge("trend", "combiner")
    workflow.add_edge("combiner", END)
    
    return workflow.compile()


# =============================================================================
# Public API
# =============================================================================

def process_metric(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process metrics through the agent.
    
    Args:
        metrics: Dict of metric values (e.g., cpu_usage_percent, memory_usage_percent, etc.)
    
    Returns:
        Combined output with analyzer and trend analysis results
    """
    graph = build_metrics_graph()
    
    initial_state: MetricsState = {
        "raw_metrics": metrics,
        "timestamp": datetime.now().isoformat(),
        "analyzer_output": None,
        "trend_output": None,
        "combined_output": None,
    }
    
    result = graph.invoke(initial_state)
    return result.get("combined_output", {})


def reset_trend_analyzer():
    """Reset the trend analyzer's sliding window (useful for testing)"""
    global trend_analyzer
    trend_analyzer = TrendAnalyzer()
