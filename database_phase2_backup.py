import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(_file_).parent
DATA_DIR = BASE_DIR / "data"

DB_PATH = DATA_DIR / "expenses.db"
JSON_PATH = DATA_DIR / "expenses.json"


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM expenses"
        ).fetchone()[0]

        if count == 0 and JSON_PATH.exists():
            with open(JSON_PATH, "r", encoding="utf-8") as file:
                expenses = json.load(file)

            for expense in expenses:
                conn.execute("""
                    INSERT INTO expenses
                    (amount, category, description, date)
                    VALUES (?, ?, ?, ?)
                """, (
                    expense["amount"],
                    expense["category"],
                    expense["description"],
                    expense["date"]
                ))

    print("Database initialized successfully!")


if _name_ == "_main_":
    initialize_database()