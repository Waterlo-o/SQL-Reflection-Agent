from langgraph.graph import END, START, StateGraph

from sql_reflection_agent.nodes import execute_sql_node, generate_sql_node

from sql_reflection_agent.state import SQLAgentState


def build_graph():
    workflow = StateGraph(SQLAgentState)

    workflow.add_node("generate", generate_sql_node)
    workflow.add_node("execute", execute_sql_node)

    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", "execute")
    workflow.add_edge("execute", END)
        
    app = workflow.compile()
    
    return app
