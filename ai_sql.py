"""AI layer: turns plain-English questions into safe, read-only SQL and explains results."""
import os
import re
import sqlite3

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found. Create a .env file in this folder with the line: "
        "GROQ_API_KEY=your_key_here"
    )

client = Groq(api_key=API_KEY)
MODEL = "openai/gpt-oss-120b"
DB_PATH = "sales.db"

SCHEMA = """Table sales(order_id, order_date TEXT 'YYYY-MM-DD', ship_mode, segment,
city, state, region, category, sub_category, sales REAL, quantity, discount REAL, profit REAL).
Regions: Central, East, South, West.
Categories: Furniture, Office Supplies, Technology."""


def _chat(system: str, user: str) -> str:
    """Send one prompt to the LLM and return its text reply."""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


def question_to_sql(question: str) -> str:
    """Convert a plain-English question into a single SQLite SELECT query."""
    sql = _chat(
        "You write SQLite queries using only this schema: " + SCHEMA +
        " Return exactly one SELECT statement and nothing else. "
        "Add LIMIT 50 unless all rows are needed.",
        question,
    )
    sql = re.sub(r"```(?:sql)?", "", sql).strip()  # remove markdown fences
    return sql.rstrip(";").strip()


def is_safe(sql: str) -> bool:
    """Allow only a single read-only SELECT statement."""
    s = sql.lower().strip()
    banned = r"\b(drop|delete|update|insert|alter|attach|pragma|create|replace|vacuum)\b"
    return s.startswith("select") and ";" not in s and not re.search(banned, s)


def run_query(sql: str) -> pd.DataFrame:
    """Run the query on a read-only connection (second layer of protection)."""
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return pd.read_sql(sql, con)
    finally:
        con.close()


def explain(question: str, df: pd.DataFrame) -> str:
    """Explain the query result in plain English for a manager."""
    return _chat(
        "You are a business analyst. Explain the result in 2 short sentences "
        "for a manager. Use only the numbers shown; do not invent any.",
        f"Question: {question}\nResult:\n{df.head(20).to_string(index=False)}",
    )


def generate_insights(facts: str) -> str:
    """Turn a few computed facts into findings and recommendations."""
    return _chat(
        "You are a consulting analyst. From the facts, write exactly 3 key findings "
        "and 2 recommendations as short bullet points. Use only the numbers given; "
        "do not invent any.",
        facts,
    )