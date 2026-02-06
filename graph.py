from langgraph.graph import StateGraph, END
from state import IncidentState

from agents.commander import commander_agent
from agents.logs_agent import logs_agent
from agents.metrics_agent import metrics_agent
from agents.deploy_agent import deploy_agent

from core.correlation import correlate
from core.decision import decide
from core.action import act
from core.report import report

graph = StateGraph(IncidentState)

graph.add_node("commander", commander_agent)
graph.add_node("logs", logs_agent)
graph.add_node("metrics", metrics_agent)
graph.add_node("deploy", deploy_agent)
graph.add_node("correlate", correlate)
graph.add_node("decide", decide)
graph.add_node("act", act)
graph.add_node("report", report)

graph.set_entry_point("commander")

graph.add_edge("commander", "logs")
graph.add_edge("commander", "metrics")
graph.add_edge("commander", "deploy")

graph.add_edge("logs", "correlate")
graph.add_edge("metrics", "correlate")
graph.add_edge("deploy", "correlate")

graph.add_edge("correlate", "decide")
graph.add_edge("decide", "act")
graph.add_edge("act", "report")
graph.add_edge("report", END)

app = graph.compile()

