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


def get_table_data(table_name: str, limit: int = 50) -> dict:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            [table_name],
        )
        if not cursor.fetchone():
            return {"error": f"Table '{table_name}' hasn't been found."}
        cursor.execute(
            f"SELECT * FROM {table_name} LIMIT ?",
            [
                limit,
            ],
        )
        rows = cursor.fetchall()

        columns = [decs[0] for decs in cursor.description]

        return {"columns": columns, "rows": rows}

    except sqlite3.Error as e:
        return {"error": str(e)}
    finally:
        conn.close()
