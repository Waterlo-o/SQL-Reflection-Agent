import sqlite3


DB_DIR = "data"
DB_PATH = f"{DB_DIR}/agent_test.db"

def execute_sql(query: str) -> tuple[bool, str]:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return True, str(rows)
    except sqlite3.Error as e:
        return False, str(e)
    finally:
        conn.close()


def get_schema() -> str:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type = 'table'")
        rows = cursor.fetchall()
        return "\n\n".join(row[0] for row in rows)
    finally:
        conn.close()

