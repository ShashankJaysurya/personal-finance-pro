import sqlite3
import json
from datetime import datetime
from pathlib import Path

from data.database import add_expense as add_expense_db

from data.database import update_expense as update_expense_db

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "expenses.db"
JSON_PATH = DATA_DIR / "expenses.json"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)


def migrate_json_data():
    with get_connection() as conn:
        status = conn.execute(
            "SELECT setting_value FROM app_settings "
            "WHERE setting_key = 'json_migration'"
        ).fetchone()

        if status:
            return

        if not JSON_PATH.exists():
            return

        try:
            with open(JSON_PATH, "r", encoding="utf-8") as file:
                expenses = json.load(file)

            if not isinstance(expenses, list):
                print("JSON migration skipped: unexpected file format.")
                return

            existing = conn.execute(
                "SELECT COUNT(*) FROM expenses"
            ).fetchone()[0]

            # Avoid importing records twice.
            if existing == 0:
                for expense in expenses:
                    conn.execute("""
                        INSERT INTO expenses
                        (amount, category, description, date)
                        VALUES (?, ?, ?, ?)
                    """, (
                        float(expense["amount"]),
                        str(expense["category"]),
                        str(expense["description"]),
                        str(expense["date"])
                    ))

            conn.execute("""
                INSERT INTO app_settings
                (setting_key, setting_value)
                VALUES ('json_migration', 'completed')
            """)

            print("Existing expense records checked successfully!")

        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as error:
            print(f"JSON migration error: {error}")


def add_expense():
    print("\n--- ADD NEW EXPENSE ---")

    try:
        amount = float(input("Enter amount (INR): "))

        if amount <= 0:
            print("Amount must be greater than zero.")
            return

        category = input("Enter category: ").strip()
        description = input("Enter description: ").strip()

        if not category or not description:
            print("Category and description cannot be empty.")
            return

        expense_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        expense_id = add_expense_db(
            amount,
            category,
            description,
            expense_date
)

        print("\nExpense saved successfully!")

    except ValueError:
        print("Please enter a valid numeric amount.")


def view_expenses():
    print("\n--- YOUR EXPENSES ---")

    with get_connection() as conn:
        expenses = conn.execute(
            "SELECT * FROM expenses ORDER BY id"
        ).fetchall()

    if not expenses:
        print("No expenses recorded yet.")
        return

    for expense in expenses:
        print(f"\nExpense ID: {expense['id']}")
        print(f"Amount: INR {expense['amount']:.2f}")
        print(f"Category: {expense['category']}")
        print(f"Description: {expense['description']}")
        print(f"Date: {expense['date']}")

    print(f"\nTotal records: {len(expenses)}")


def total_spending():
    with get_connection() as conn:
        result = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
        ).fetchone()

    print("\n--- TOTAL SPENDING ---")
    print(f"Total Expenses: INR {result['total']:.2f}")


def edit_expense():
    view_expenses()

    try:
        expense_id = int(input("\nEnter Expense ID to edit: "))

        with get_connection() as conn:
            expense = conn.execute(
                "SELECT * FROM expenses WHERE id = ?",
                (expense_id,)
            ).fetchone()

            if not expense:
                print("Expense ID not found.")
                return

            print("\nPress Enter to keep the existing value.")

            amount_input = input(
                f"Amount [{expense['amount']}]: "
            ).strip()

            category_input = input(
                f"Category [{expense['category']}]: "
            ).strip()

            description_input = input(
                f"Description [{expense['description']}]: "
            ).strip()

            amount = (
                float(amount_input)
                if amount_input else expense["amount"]
            )

            if amount <= 0:
                print("Amount must be greater than zero.")
                return

            category = category_input or expense["category"]
            description = description_input or expense["description"]

            update_expense_db(
                expense_id,
                amount,
                category,
                description,
                expense["date"]
)

        print("Expense updated successfully!")

    except ValueError:
        print("Please enter a valid ID and amount.")


def delete_expense():
    view_expenses()

    try:
        expense_id = int(input("\nEnter Expense ID to delete: "))

        with get_connection() as conn:
            expense = conn.execute(
                "SELECT * FROM expenses WHERE id = ?",
                (expense_id,)
            ).fetchone()

            if not expense:
                print("Expense ID not found.")
                return

            confirm = input(
                f"Delete INR {expense['amount']:.2f}? (yes/no): "
            ).strip().lower()

            if confirm == "yes":
                conn.execute(
                    "DELETE FROM expenses WHERE id = ?",
                    (expense_id,)
                )
                print("Expense deleted successfully!")
            else:
                print("Deletion cancelled.")

    except ValueError:
        print("Please enter a valid Expense ID.")

def category_analytics():
    print("\n--- CATEGORY-WISE SPENDING ANALYTICS ---")

    with get_connection() as conn:
        results = conn.execute("""
            SELECT category, SUM(amount), COUNT(*)
            FROM expenses
            GROUP BY category
            ORDER BY SUM(amount) DESC
        """).fetchall()

    if not results:
        print("No expenses available.")
        return

    grand_total = sum(row[1] for row in results)

    for category, amount, count in results:
        percentage = (amount / grand_total) * 100
        print(f"\nCategory: {category}")
        print(f"Spending: INR {amount:.2f}")
        print(f"Transactions: {count}")
        print(f"Share: {percentage:.1f}%")

    print(f"\nTotal Spending: INR {grand_total:.2f}")

def monthly_spending_analytics():
    print("\n--- MONTHLY SPENDING ANALYTICS ---")

    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT
                substr(date, 1, 7) AS month,
                SUM(amount) AS total,
                COUNT(*) AS transactions
            FROM expenses
            GROUP BY substr(date, 1, 7)
            ORDER BY month
        """).fetchall()

    finally:
        conn.close()

    if not rows:
        print("No expense records available.")
        return

    grand_total = sum(row[1] for row in rows)

    print("\n--- MONTH-WISE SPENDING REPORT ---")

    for month, amount, transactions in rows:
        print(f"\nMonth: {month}")
        print(f"Total Spending: INR {amount:.2f}")
        print(f"Transactions: {transactions}")

    highest_month = max(rows, key=lambda row: row[1])
    average = grand_total / len(rows)

    print("\n========== SUMMARY ==========")
    print(f"Total Spending: INR {grand_total:.2f}")
    print(f"Highest Spending Month: {highest_month[0]}")
    print(f"Highest Monthly Spending: INR {highest_month[1]:.2f}")
    print(f"Average Monthly Spending: INR {average:.2f}")
    print("=============================")
def main():
    initialize_database()
    migrate_json_data()

    while True:
        print("\n==============================")
        print("      PYTHON EXPENSE TRACKER")
        print("==============================")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Total Spending")
        print("4. Edit Expense")
        print("5. Delete Expense")
        print("6. Exit")
        print("7. Category Analytics")
        print("8. Monthly Spending Analytics")

        choice = input("\nEnter your choice (1-8): ").strip()

        if choice == "1":
            add_expense()

        elif choice == "2":
            view_expenses()

        elif choice == "3":
            total_spending()

        elif choice == "4":
            edit_expense()

        elif choice == "5":
            delete_expense()

        elif choice == "6":
            print("Thank you for using Expense Tracker!")
            break

        elif choice == "7":
            category_analytics()

        elif choice == "8":
            monthly_spending_analytics()

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()