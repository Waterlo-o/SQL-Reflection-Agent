import json
import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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


@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):

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

    async def event_generator():
        final_state = None

        async for event_type, event_data in agent_app.astream(
            initial_state, stream_mode=["custom", "values"]
        ):
            if event_type == "custom":
                if isinstance(event_data, str):
                    chunk_data = json.dumps({"text": event_data})
                    yield f"event: message\ndata: {chunk_data}\n\n"
            elif event_type == "values":
                final_state = event_data
        if final_state and isinstance(final_state, dict):
            save_and_print_log(final_state)
            answer_text = final_state.get("final_answer", "")
            final_payload = {
                "final_answer": answer_text,
                "history": final_state.get("history", []),
            }

            yield f"event: complete\ndata: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/data/{table_name}", response_model=TableDataResponse)
def api_get_table_data(table_name: str):
    table = get_table_data(table_name)

    if "error" in table:
        return TableDataResponse(error=table["error"])

    return TableDataResponse(columns=table["columns"], rows=table["rows"])
