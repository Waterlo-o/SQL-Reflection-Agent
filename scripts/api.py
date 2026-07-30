import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(os.path.join(project_root, "src"))

from sql_reflection_agent.db import get_schema, get_table_data
from sql_reflection_agent.graph import build_graph
from sql_reflection_agent.reporting import save_and_print_log
from sql_reflection_agent.state import SQLAgentState

load_dotenv()


agent_app = build_graph()


app = FastAPI(title="SQL Agent API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    history: list


class TableDataResponse(BaseModel):
    columns: list[str] = []
    rows: list[list] = []
    error: str = ""


@app.get("/api/schema")
def api_get_schema():
    return {"schema": get_schema()}


@app.post("/api/chat", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest):

    initial_state: SQLAgentState = {
        "question": request.question,
        "schema": get_schema(),
        "attempt_count": 0,
        "sql_query": "",
        "critic_feedback": "",
        "is_approved": False,
        "is_valid": False,
        "execution_result": "",
        "final_answer": "",
        "history": [],
    }

    final_state = agent_app.invoke(initial_state)

    save_and_print_log(final_state)

    return ChatResponse(
        answer=final_state["final_answer"], history=final_state["history"]
    )


@app.get("/api/data/{table_name}", response_model=TableDataResponse)
def api_get_table_data(table_name: str):
    table = get_table_data(table_name)

    if "error" in table:
        return TableDataResponse(error=table["error"])

    return TableDataResponse(columns=table["columns"], rows=table["rows"])
