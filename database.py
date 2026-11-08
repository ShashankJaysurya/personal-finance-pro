import json
import sqlite3
from pathlib import Path

# Correct Python special variable: __file__ (two underscores on each side)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DB_PATH = DATA_DIR / "expenses.db"
JSON_PATH = DATA_DIR / "expenses.json"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH), timeout=10)


def initialize_database():
    """
    Create the expenses table only if it does not exist.
    Existing rows are never deleted or overwritten.
    JSON import happens only when the expenses table is empty.
    """
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
                    expense.get("description", ""),
                    expense["date"],
                ))

    print(f"Database initialized: {DB_PATH}")


# Correct Python special variable: __name__ (two underscores on each side)
if __name__ == "__main__":
    initialize_database()
