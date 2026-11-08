from data.database import (
    initialize_database,
    add_expense,
    get_expenses,
    update_expense,
    delete_expense
)

initialize_database()

print("\n--- SQLITE CRUD TEST ---")

# TEST 1: ADD EXPENSE
expense_id = add_expense(
    123.45,
    "Testing",
    "SQLite test expense",
    "2026-11-08"
)

print("ADD: Successful. ID:", expense_id)

try:
    # TEST 2: READ EXPENSE
    expenses = get_expenses()

    record = next(
        (e for e in expenses if e["id"] == expense_id),
        None
    )

    assert record is not None
    print("READ: Successful.", record)

    # TEST 3: UPDATE EXPENSE
    updated = update_expense(
        expense_id,
        150.00,
        "Testing",
        "Updated SQLite test",
        "2026-11-08"
    )

    assert updated
    print("UPDATE: Successful.")

    # Verify updated amount
    record = next(
        e for e in get_expenses()
        if e["id"] == expense_id
    )

    assert record["amount"] == 150.00
    print("UPDATE VERIFIED:", record)

    # TEST 4: DELETE EXPENSE
    deleted = delete_expense(expense_id)

    assert deleted
    print("DELETE: Successful.")

    print("\nALL SQLITE CRUD TESTS PASSED!")

finally:
    # Remove test record if it still exists
    if any(
        e["id"] == expense_id
        for e in get_expenses()
    ):
        delete_expense(expense_id)