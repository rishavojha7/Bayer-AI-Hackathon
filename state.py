from typing import TypedDict, Dict, Any, List, Optional

class IncidentState(TypedDict):
    alert: Dict[str, Any]

    logs_data: List[str]
    metrics_data: Dict[str, Any]
    deploy_data: Dict[str, Any]

    logs_findings: Optional[Dict[str, Any]]
    metrics_findings: Optional[Dict[str, Any]]
    deploy_findings: Optional[Dict[str, Any]]

    root_cause: Optional[str]
    confidence: Optional[float]

    decision: Optional[str]
    action: Optional[Dict[str, Any]]

    report: Optional[str]
