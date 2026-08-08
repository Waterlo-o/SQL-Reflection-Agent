import json
import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langgraph.config import get_stream_writer

from sql_reflection_agent.consts import MAX_ATTEMPTS
from sql_reflection_agent.db import execute_sql
from sql_reflection_agent.prompts import (
    CRITIC_SYSTEM_PROMPT,
    EXECUTOR_SYSTEM_PROMPT,
    FORMULATE_ANSWER_SYSTEM_PROMPT,
)
from sql_reflection_agent.state import CriticVerdict, SQLAgentState

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=API_KEY)
    return _client


logger = logging.getLogger(__name__)


async def generate_sql_node(state: SQLAgentState) -> dict:

    full_instruction = f"{EXECUTOR_SYSTEM_PROMPT}\n\nSchema:\n{state['schema']}"

    if state["attempt_count"] == 0:
        contents = f"Question: {state['question']}"
    else:
        contents = (
            f"Question: {state['question']}\n\n"
            f"Your previous SQL query: {state['sql_query']}\n\n"
            f"Critic feedback on that query: {state['critic_feedback']}\n\n"
            f"Write a corrected query that addresses this feedback."
        )

    response = await get_client().aio.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=full_instruction,
            max_output_tokens=1500,
        ),
    )

    if response.usage_metadata:
        logger.info(
            f"Token usage — prompt: {response.usage_metadata.prompt_token_count}, "
            f"response: {response.usage_metadata.candidates_token_count}, "
            f"total: {response.usage_metadata.total_token_count}"
        )

    raw_query = response.text
    if not raw_query:
        raise ValueError("Gemini couldn't return valid answer")

    clean_query = raw_query.strip()
    clean_query = clean_query.removeprefix("```sql")
    clean_query = clean_query.removeprefix("```")
    clean_query = clean_query.removesuffix("```")
    clean_query = clean_query.strip()

    current_try = state["attempt_count"] + 1

    return {"sql_query": clean_query, "attempt_count": current_try}


def execute_sql_node(state: SQLAgentState) -> dict:

    query = state["sql_query"]

    is_success, execution_result = execute_sql(query)

    return {"is_valid": is_success, "execution_result": execution_result}


async def critic_node(state: SQLAgentState) -> dict:

    full_instruction = f"{CRITIC_SYSTEM_PROMPT} \n\nSchema:\n{state['schema']}"

    full_history = f"user_question: {state['question']}\n\nagent_answer: {state['sql_query']}\n\nsql_answer: {state['execution_result']}\n\nsql_answer_status: {state['is_valid']}"

    response = await get_client().aio.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=full_history,
        config=types.GenerateContentConfig(
            system_instruction=full_instruction,
            max_output_tokens=1500,
            response_mime_type="application/json",
            response_schema=CriticVerdict,
        ),
    )

    if not response.text:
        logger.error("No text in critic answer")
        return {
            "critic_feedback": "Something went wrong, gemini could not answer your question."
        }

    critic_answer = json.loads(response.text)

    current_step_log = {
        "attempt": state["attempt_count"],
        "query": state["sql_query"],
        "db_result": state["execution_result"],
        "is_valid": state["is_valid"],
        "critic_reasoning": critic_answer.get("reasoning", ""),
        "critic_feedback": critic_answer.get("feedback", ""),
        "is_approved": critic_answer.get("is_approved", False),
    }

    print(critic_answer["reasoning"])

    return {
        "is_approved": critic_answer["is_approved"],
        "critic_feedback": critic_answer["feedback"],
        "history": [current_step_log],
    }


def formulate_error_node(state: SQLAgentState) -> dict:
    message = f"Could not generate a valid query after {MAX_ATTEMPTS} attempts. Latest critic feedback: {state['critic_feedback']}"
    return {"final_answer": message}


async def formulate_answer_node(state: SQLAgentState) -> dict:

    writer = get_stream_writer()
    full_text = ""

    full_history = (
        f"user_question: {state['question']}\n\n"
        f"agent_answer: {state['sql_query']}\n\n"
        f"sql_answer: {state['execution_result']}\n\n"
        f"sql_answer_status: {state['is_valid']}\n\n"
        f"critic_feedback: {state['critic_feedback']}"
    )
    system_prompt = FORMULATE_ANSWER_SYSTEM_PROMPT

    async for chunk in await get_client().aio.models.generate_content_stream(
        model="gemini-3.1-flash-lite",
        contents=full_history,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1500,
        ),
    ):
        if chunk.text:
            full_text += chunk.text
            writer(chunk.text)

    return {"final_answer": full_text}
