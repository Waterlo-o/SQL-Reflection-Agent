import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(os.path.join(project_root, "src"))


import streamlit as st
from dotenv import load_dotenv

from sql_reflection_agent.graph import build_graph
from sql_reflection_agent.state import SQLAgentState

load_dotenv()


@st.cache_resource
def get_agent_app():
    return build_graph()


app = get_agent_app()

DB_SCHEMA = """
Таблица clients:
- id (INTEGER, PRIMARY KEY)
- name (TEXT)
- email (TEXT)
- created_at (DATETIME)
"""

st.set_page_config(page_title="SQL AI Agent", page_icon="🤖")

st.title("🤖 Умный SQL-Агент")
st.markdown(
    "Задай вопрос на естественном языке, а агент сам напишет SQL-запрос, проверит его и выдаст ответ."
)

user_question = st.text_input(
    "Ваш вопрос к базе данных:", placeholder="Например: Сколько всего клиентов в базе?"
)

if st.button("Спросить"):
    if user_question:
        with st.spinner("Агент думает, пишет SQL и проверяет его..."):
            initial_state: SQLAgentState = {
                "question": user_question,
                "schema": DB_SCHEMA,
                "attempt_count": 0,
                "sql_query": "",
                "critic_feedback": "",
                "is_approved": False,
                "is_valid": False,
                "execution_result": "",
                "final_answer": "",
                "history": [],
            }

            # Запускаем графа
            final_state = app.invoke(initial_state)

        # Выводим финальный ответ
        st.success("Готово!")
        st.markdown("### 🎯 Ответ:")
        st.write(final_state["final_answer"])

        with st.expander("Посмотреть ход мыслей агента 🧠"):
            history = final_state.get("history", [])
            for step in history:
                st.markdown(f"**Попытка {step['attempt']}**")
                st.code(step["query"], language="sql")

                status_emoji = "✅ Успех" if step["is_valid"] else "❌ Ошибка"
                st.markdown(f"**Ответ базы ({status_emoji}):**")
                st.code(step["db_result"], language="text")

                st.markdown(f"**Логика критика:** {step['critic_reasoning']}")
                st.markdown("---")
    else:
        st.warning("Пожалуйста, введите вопрос.")
