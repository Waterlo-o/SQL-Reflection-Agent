import json
from typing import cast
from unittest.mock import MagicMock, patch

from sql_reflection_agent.nodes import (
    SQLAgentState,
    critic_node,
    execute_sql_node,
    formulate_answer_node,
    formulate_error_node,
    generate_sql_node,
)


@patch("sql_reflection_agent.nodes.get_client")
def test_generate_sql_node_cleans_query_and_increments(mock_get_client):
    fake_response = MagicMock()
    fake_response.text = "```sql\nSELECT * FROM clients;\n```"
    fake_response.usage_metadata = None
    mock_get_client.return_value.models.generate_content.return_value = fake_response

    initial_state: SQLAgentState = {
        "question": "How much users?",
        "schema": "Table users",
        "attempt_count": 0,
        "sql_query": "",
        "critic_feedback": "",
        "is_approved": False,
        "is_valid": False,
        "execution_result": "",
        "final_answer": "",
        "history": [],
    }

    result = generate_sql_node(state=initial_state)

    assert result["attempt_count"] == 1
    assert result["sql_query"] == "SELECT * FROM clients;"


@patch("sql_reflection_agent.nodes.client")
def test_critic_node(mock_client):

    fake_response = MagicMock()

    fake_response.text = json.dumps(
        {
            "reasoning": "Whatever reason it is",
            "is_approved": True,
            "feedback": "Whatever feedback it is",
        }
    )

    mock_client.models.generate_content.return_value = fake_response

    initial_state: SQLAgentState = {
        "question": "How much users?",
        "schema": "Table users",
        "attempt_count": 0,
        "sql_query": "",
        "critic_feedback": "",
        "is_approved": False,
        "is_valid": False,
        "execution_result": "",
        "final_answer": "",
        "history": [],
    }

    result = critic_node(initial_state)

    assert result["is_approved"] is True
    assert result["critic_feedback"] == "Whatever feedback it is"


@patch("sql_reflection_agent.nodes.execute_sql")
def test_execute_sql_node_success(mock_execute_sql):

    mock_execute_sql.return_value = (True, "[(19,)]")

    initial_state = {"sql_query": "SELECT COUNT(*) FROM clients;"}

    result = execute_sql_node(cast(SQLAgentState, initial_state))

    assert result["is_valid"] is True
    assert result["execution_result"] == "[(19,)]"

    mock_execute_sql.assert_called_once_with("SELECT COUNT(*) FROM clients;")


@patch("sql_reflection_agent.nodes.execute_sql")
def test_execute_sql_node_failure(mock_execute_sql):

    mock_execute_sql.return_value = (False, "sqlite3.Error: no such column: address")
    initial_state = {"sql_query": "SELECT address FROM clients;"}

    result = execute_sql_node(cast(SQLAgentState, initial_state))

    assert result["is_valid"] is False
    assert result["execution_result"] == "sqlite3.Error: no such column: address"


def test_formulate_error_node():

    initial_state = {
        "critic_feedback": "You are trying to use JSON, from place where it not suppoce to be"
    }

    result = formulate_error_node(cast(SQLAgentState, initial_state))

    assert "You are trying to use JSON" in result["final_answer"]
    assert "Could not generate a valid query" in result["final_answer"]


@patch("sql_reflection_agent.nodes.client")
def test_formulate_answer_node(mock_client):

    fake_response = MagicMock()
    fake_response.text = "19 clients in total were find."
    mock_client.models.generate_content.return_value = fake_response

    initial_state: SQLAgentState = {
        "question": "How nuch clients is there in total?",
        "sql_query": "SELECT COUNT(*) FROM clients;",
        "execution_result": "[(19,)]",
        "is_valid": True,
        "critic_feedback": "Great answer",
        "schema": "",
        "attempt_count": 1,
        "is_approved": True,
        "final_answer": "",
        "history": [],
    }

    result = formulate_answer_node(cast(SQLAgentState, initial_state))

    assert result["final_answer"] == "19 clients in total were find."
