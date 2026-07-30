from typing import cast

from sql_reflection_agent.graph import route_after_critic
from sql_reflection_agent.state import SQLAgentState


def make_state(**overrides) -> SQLAgentState:
    base_state: SQLAgentState = {
        "question": "test question",
        "sql_query": "",
        "schema": "schema",
        "is_valid": True,
        "execution_result": "",
        "attempt_count": 1,
        "critic_feedback": "",
        "is_approved": False,
        "final_answer": "",
        "history": [],
    }
    return cast(SQLAgentState, {**base_state, **overrides})


def test_route_after_critic_when_approved():
    state = make_state(is_approved=True, attempt_count=1)
    result = route_after_critic(state)
    assert result == "formulate"


def test_route_after_critic_when_retry_available():
    state = make_state(is_approved=False, attempt_count=1)
    result = route_after_critic(state)
    assert result == "retry"


def test_route_after_critic_when_max_attempts_reached():
    state = make_state(is_approved=False, attempt_count=4)
    result = route_after_critic(state)
    assert result == "fail"
