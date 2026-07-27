import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from sql_reflection_agent.db import get_schema
from sql_reflection_agent.graph import build_graph
from sql_reflection_agent.state import SQLAgentState


def main():
    app = build_graph()

    schema = get_schema()

    initial_state: SQLAgentState = {
        "question": "Сколько всего клиентов в базе?",
        "sql_query": "",
        "schema": schema,
        "is_valid": False,
        "execution_result": ""
    }

    print(f"🚀 Запускаем агента. Вопрос: '{initial_state['question']}'")

    result = app.invoke(initial_state)

    print("\n" + "="*50)
    print("🎯 РЕЗУЛЬТАТ РАБОТЫ АГЕНТА:")
    print("="*50)
    print(f"Сгенерированный SQL:\n{result.get('sql_query')}")
    print("-" * 50)
    print(f"Выполнилось без ошибок?: {result.get('is_valid')}")
    print(f"Ответ из БД:\n{result.get('execution_result')}")
    print("="*50)

if __name__ == "__main__":
    main()