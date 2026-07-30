import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel


class SQLAgentState(TypedDict):
    question: str
    schema: str
    sql_query: str
    is_valid: bool
    execution_result: str
    attempt_count: int
    critic_feedback: str
    is_approved: bool
    final_answer: str
    history: Annotated[list, operator.add]


class CriticVerdict(BaseModel):
    reasoning: str
    is_approved: bool
    feedback: str
