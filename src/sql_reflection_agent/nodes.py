import logging
import os
import sqlite3

from dotenv import load_dotenv
from google import genai
from google.genai import types

from config.prompts import EXECUTOR_SYSTEM_PROMPT
from scripts.seed_db import DB_PATH
from sql_reflection_agent.db import execute_sql
from sql_reflection_agent.state import SQLAgentState

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

logger = logging.getLogger(__name__)


def generate_sql_node(state: SQLAgentState) -> dict:

    full_instruction = f"{EXECUTOR_SYSTEM_PROMPT}\n\nСхема базы:\n{state['schema']}"

    query = state["question"]

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=query,
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


    return {"sql_query": clean_query}


def execute_sql_node(state: SQLAgentState) -> dict:

    query = state['sql_query']

    is_success, execution_result = execute_sql(query)

    return {
        "is_valid": is_success,
        "execution_result": execution_result
    }
