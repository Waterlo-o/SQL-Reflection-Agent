from typing import TypedDict



class SQLAgentState(TypedDict):
    question: str
    sql_query: str
    schema: str
    is_valid: bool
    execution_result: str