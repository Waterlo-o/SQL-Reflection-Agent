import os
from dotenv import load_dotenv


from sql_reflection_agent.graph import build_graph
from sql_reflection_agent.state import SQLAgentState
from sql_reflection_agent.db import get_schema
from sql_reflection_agent.reporting import save_and_print_log


def main():
    load_dotenv()

    app = build_graph()

    db_schema = get_schema()

    user_question = "How many cliants in the DB?"


    initial_state: SQLAgentState = {
        "question": user_question,
        "schema": db_schema,
        "attempt_count": 0,
        "sql_query": "",
        "critic_feedback": "",
        "is_approved": False,
        "is_valid": False,
        "execution_result": "",
        "final_answer": "",
        "history": [] 
    }

    print("🤖 Booting the SQL-Agent... (it may take a few seconds)")
    print("-" * 50)

    final_state = app.invoke(initial_state)

    save_and_print_log(final_state)


if __name__ == "__main__":
    main()