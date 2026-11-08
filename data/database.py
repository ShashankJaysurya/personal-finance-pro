import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
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

def add_expense(amount, category, description, date):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO expenses
            (amount, category, description, date)
            VALUES (?, ?, ?, ?)
            """,
            (amount, category, description, date)
        )

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()

def get_expenses():
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute(
            """
            SELECT id, amount, category, description, date
            FROM expenses
            ORDER BY date DESC, id DESC
            """
        )

        expenses = cursor.fetchall()

        return [dict(expense) for expense in expenses]

    finally:
        conn.close()
        
def delete_expense(expense_id):
    conn = get_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()

def update_expense(expense_id, amount, category, description, date):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            UPDATE expenses
            SET amount = ?, category = ?, description = ?, date = ?
            WHERE id = ?
            """,
            (amount, category, description, date, expense_id)
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()