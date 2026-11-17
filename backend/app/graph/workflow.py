from langgraph.graph import StateGraph, END
from app.graph.state import WorkflowState
from app.graph.nodes import (
    planner_node,
    code_generator_node,
    code_reviewer_node,
    test_generator_node,
    execution_node,
    debugger_node,
    explainer_node,
    route_after_execution,
    route_after_debugger
)

def create_autonomous_software_graph():
    """Build and compile the LangGraph multi-agent workflow."""
    workflow = StateGraph(WorkflowState)

    # Register all agent and tool nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("code_generator", code_generator_node)
    workflow.add_node("code_reviewer", code_reviewer_node)
    workflow.add_node("test_generator", test_generator_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("debugger", debugger_node)
    workflow.add_node("explainer", explainer_node)

    # Workflow entry point
    workflow.set_entry_point("planner")

    # Primary pipeline
    workflow.add_edge("planner", "code_generator")
    workflow.add_edge("code_generator", "code_reviewer")
    workflow.add_edge("code_reviewer", "test_generator")
    workflow.add_edge("test_generator", "execution")

    # Dynamic conditional branching
    workflow.add_conditional_edges(
        "execution",
        route_after_execution,
        {
            "debugger": "debugger",
            "explainer": "explainer"
        }
    )

    # Debugger loopback for re-validation
    workflow.add_conditional_edges(
        "debugger",
        route_after_debugger,
        {
            "execution": "execution",
            "explainer": "explainer"
        }
    )

    workflow.add_edge("explainer", END)

    return workflow.compile()

autonomous_graph = create_autonomous_software_graph()
