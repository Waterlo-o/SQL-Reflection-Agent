from typing import Literal

from langgraph.graph import END, START, StateGraph

from sql_reflection_agent.nodes import execute_sql_node, generate_sql_node, critic_node, formulate_error_node, formulate_answer_node

from sql_reflection_agent.consts import MAX_ATTEMPTS

from sql_reflection_agent.state import SQLAgentState


def build_graph():
    workflow = StateGraph(SQLAgentState)

    workflow.add_node("generate", generate_sql_node)
    workflow.add_node("execute", execute_sql_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("formulate_error", formulate_error_node)
    workflow.add_node("formulate_answer", formulate_answer_node)

    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", "execute")
    workflow.add_edge("execute", "critic")
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "formulate": "formulate_answer",
            "retry": "generate",
            "fail": "formulate_error"
        }
    )
    workflow.add_edge("formulate_error", END)
    workflow.add_edge("formulate_answer", END)
        
    app = workflow.compile()
    
    return app


def route_after_critic(state: SQLAgentState) -> Literal["formulate", "retry", "fail"]:

    if state["is_approved"]:
        return "formulate"
    elif not state["is_approved"] and state["attempt_count"] < MAX_ATTEMPTS:
        return "retry"
    else:
        return "fail"