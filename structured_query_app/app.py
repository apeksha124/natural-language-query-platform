import os
import re
import textwrap
from typing import Optional, Tuple
import streamlit as st
import pandas as pd
import sqlite3

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except Exception:
    mysql = None
    MySQLError = Exception  
DEFAULT_MODEL = os.getenv("LOCAL_MODEL_PATH", "/path/to/model.gguf")
DEFAULT_LIMIT = int(os.getenv("NL_SQL_MAX_ROWS", "200"))
st.set_page_config(page_title="NL → SQL (Offline)", layout="wide")
st.title("🔒 NL → SQL (Offline) — CSV & MySQL")

# --- Utility functions ---
def clean_sql_output(sql_text: str) -> str:
    """Clean LLM output: remove code fences, 'SQL:' prefix, backticks, and trailing semicolons."""
    if not sql_text:
        return ""
    s = sql_text.strip()
    s = re.sub(r'^\s*SQL\s*[:\-]\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'```(?:sql|\w+)?\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s*```$', '', s, flags=re.IGNORECASE)
    s = s.replace("`", "")
    match = re.search(r'(SELECT\b.*)', s, flags=re.IGNORECASE | re.DOTALL)
    if match:
        s = match.group(1)
    s = re.sub(r';+\s*$', '', s).strip()
    return s

FORBIDDEN_RE = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|REPLACE)\b", re.IGNORECASE)
SELECT_START_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
LIMIT_RE = re.compile(r"\bLIMIT\b", re.IGNORECASE)

def is_query_safe(sql: str) -> Tuple[bool, Optional[str]]:
    if not sql or not sql.strip():
        return False, "Empty query."
    if FORBIDDEN_RE.search(sql):
        return False, "Query contains forbidden statements (non-SELECT)."
    if not SELECT_START_RE.match(sql):
        return False, "Only SELECT queries are allowed."
    return True, None

def ensure_limit(sql: str, limit: int = DEFAULT_LIMIT) -> str:
    if LIMIT_RE.search(sql):
        return sql
    return f"{sql.rstrip()} LIMIT {limit}"

# --- LLM integration ---
def generate_sql_with_llama(nl_question: str, table_schema_text: str, model_path: str = DEFAULT_MODEL, max_tokens: int = 512) -> str:
    """
    Use llama-cpp-python to convert natural language to SQL.
    Prompt requests plain SQL with no markdown/backticks.
    """
    try:
        from llama_cpp import Llama
    except Exception as e:
        raise RuntimeError("llama-cpp-python not installed or failed to import. Install via: pip install llama-cpp-python") from e

    prompt = textwrap.dedent(f"""
    You are an expert SQL generator for MySQL/SQLite. Convert the user's natural language request
    into a single, valid SQL SELECT statement that runs on the provided schema.
    IMPORTANT: Output ONLY the SQL statement itself with no markdown, no backticks, and no explanation.
    If the user's request is ambiguous, produce a single SQL statement and (optionally) append a
    short comment starting with -- describing the ambiguity.
    Schema / Table info:
    {table_schema_text}
    User request:
    \"\"\"{nl_question}\"\"\"
    """).strip()
    llm = Llama(model_path=model_path, n_ctx=2048)
    resp = llm(prompt=prompt, max_tokens=max_tokens, temperature=0.0)
    text = None
    if isinstance(resp, dict):
        choices = resp.get("choices")
        if choices and isinstance(choices, (list, tuple)) and len(choices) > 0:
            c0 = choices[0]
            if isinstance(c0, dict):
                text = c0.get("text") or c0.get("message") or c0.get("content")
    if text is None:
        text = str(resp)
    return text.strip()

# --- DB helpers ---
def run_query_sqlite_mem(df: pd.DataFrame, sql: str, row_limit: int = DEFAULT_LIMIT) -> pd.DataFrame:
    safe, reason = is_query_safe(sql)
    if not safe:
        raise ValueError(reason)
    sql_limited = ensure_limit(sql, limit=row_limit)
    conn = sqlite3.connect(":memory:")
    try:
        df.to_sql("table_name", conn, index=False, if_exists="replace")
        res = pd.read_sql_query(sql_limited, conn)
    finally:
        conn.close()
    return res

def connect_mysql(host: str, user: str, password: str, database: str):
    if 'mysql' not in globals() and mysql is None:
        raise RuntimeError("mysql-connector-python not installed. Install via: pip install mysql-connector-python")
    try:
        conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
        if conn.is_connected():
            return conn
        raise RuntimeError("Could not connect to MySQL.")
    except MySQLError as e:
        raise RuntimeError(f"MySQL connection error: {e}") from e

def run_query_mysql(conn, sql: str, row_limit: int = DEFAULT_LIMIT) -> pd.DataFrame:
    safe, reason = is_query_safe(sql)
    if not safe:
        raise ValueError(reason)
    sql_limited = ensure_limit(sql, limit=row_limit)
    cur = conn.cursor()
    cur.execute(sql_limited)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)

def describe_table_mysql(conn, table_name: str, database: str) -> pd.DataFrame:
    query = f"""
        SELECT COLUMN_NAME AS Field,
               COLUMN_TYPE AS Type,
               IS_NULLABLE AS `Null`,
               COLUMN_KEY AS `Key`,
               COLUMN_DEFAULT AS `Default`,
               EXTRA AS Extra
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{database}'
          AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION;
    """
    return pd.read_sql(query, conn)

# --- Sidebars ---
st.sidebar.markdown("## Offline Settings")
st.sidebar.text(f"Local model path: {DEFAULT_MODEL}")
st.sidebar.text(f"Max rows limit: {DEFAULT_LIMIT}")
st.sidebar.markdown("---")
st.sidebar.markdown("Make sure you have a compatible local model and llama-cpp-python installed.")

tab_csv, tab_mysql = st.tabs(["📂 CSV (in-memory)", "🗄️ MySQL (connect)"])

# ---- CSV TAB ----
with tab_csv:
    st.header("Query an uploaded CSV (runs SQL in SQLite memory DB)")
    csv_file = st.file_uploader("Upload CSV", type=["csv"])
    if csv_file:
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")
            df = None

        if df is not None:
            st.subheader("Preview")
            st.dataframe(df.head(10))
            st.markdown(f"**Columns:** {', '.join(df.columns)}")

            user_q = st.text_input("Ask a question about the CSV (plain English)")
            if st.button("Generate SQL & Run (CSV)"):
                if not user_q or not user_q.strip():
                    st.warning("Type a natural-language question first.")
                else:
                    try:
                        schema_text = f"Table 'table_name' columns: {', '.join(df.columns)}"
                        raw_sql = generate_sql_with_llama(user_q, schema_text)
                        sql = clean_sql_output(raw_sql)
                        st.markdown("**Generated SQL:**")
                        st.code(sql, language="sql")

                        try:
                            result = run_query_sqlite_mem(df, sql)
                            st.success(f"Executed successfully — returned {len(result)} rows (capped).")
                            st.dataframe(result)
                        except Exception as exec_err:
                            st.error(f"Execution error: {exec_err}")
                            st.info("Cleaned SQL (for debugging):")
                            st.code(sql, language="sql")

                    except Exception as e:
                        st.error(f"LLM generation or runtime error: {e}")

# ---- MYSQL TAB ----
with tab_mysql:
    st.header("Connect to a local MySQL instance")
    host = st.text_input("Host", value=os.getenv("MYSQL_HOST", "localhost"))
    user = st.text_input("User", value=os.getenv("MYSQL_USER", "root"))
    password = st.text_input("Password", type="password", value=os.getenv("MYSQL_PASSWORD", ""))
    database = st.text_input("Database", value=os.getenv("MYSQL_DATABASE", ""))

    if st.button("Connect to MySQL"):
        try:
            conn = connect_mysql(host, user, password, database)
            st.session_state.conn = conn
            st.success("Connected to MySQL")
        except Exception as conn_err:
            st.error(f"Connection failed: {conn_err}")

    if 'conn' in st.session_state and st.session_state.conn:
        table_name = st.text_input("Table to inspect (for schema)")
        if table_name and st.button("Load schema for table"):
            try:
                schema_df = describe_table_mysql(st.session_state.conn, table_name, database)
                st.session_state.schema_df = schema_df
                st.dataframe(schema_df)
            except Exception as e:
                st.error(f"Could not describe table: {e}")

        user_q = st.text_input("Ask a question about the DB/table (plain English)")
        if st.button("Generate SQL & Run (MySQL)"):
            try:
                if 'schema_df' in st.session_state and table_name:
                    cols = ", ".join(f"{r['Field']} ({r['Type']})" for _, r in st.session_state.schema_df.iterrows())
                    schema_text = f"Table '{table_name}' with columns: {cols}"
                else:
                    schema_text = f"Database: {database} (no specific table schema provided)."

                raw_sql = generate_sql_with_llama(user_q, schema_text)
                sql = clean_sql_output(raw_sql)
                st.markdown("**Generated SQL:**")
                st.code(sql, language="sql")

                try:
                    result = run_query_mysql(st.session_state.conn, sql)
                    st.success(f"Executed successfully — returned {len(result)} rows (capped).")
                    st.dataframe(result)
                except Exception as exec_err:
                    st.error(f"Execution error: {exec_err}")
                    st.info("Cleaned SQL (for debugging):")
                    st.code(sql, language="sql")

            except Exception as e:
                st.error(f"LLM generation or runtime error: {e}")

