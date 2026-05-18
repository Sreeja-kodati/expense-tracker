import json
import uuid
from pathlib import Path

DB_FILE = Path(__file__).parent / "expenses.json"


def load_expenses():
    if not DB_FILE.exists():
        DB_FILE.write_text("[]", encoding="utf-8")
    try:
        with DB_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_expenses(expenses):
    with DB_FILE.open("w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2)


def create_expense(expense):
    expenses = load_expenses()
    expense_record = {
        "id": str(uuid.uuid4()),
        "item": str(expense.get("item", "Untitled")).strip(),
        "price": float(expense.get("price", 0.0)),
        "category": str(expense.get("category", "Other")).strip() or "Other",
        "date": str(expense.get("date", "")).strip(),
    }
    expenses.append(expense_record)
    save_expenses(expenses)
    return expense_record


def get_expenses():
    return load_expenses()


def update_expense(expense_id, new_data):
    expenses = load_expenses()
    updated = False
    for expense in expenses:
        if expense["id"] == expense_id:
            expense["item"] = str(new_data.get("item", expense["item"]))
            expense["price"] = float(new_data.get("price", expense["price"]))
            expense["category"] = str(new_data.get("category", expense["category"]))
            expense["date"] = str(new_data.get("date", expense["date"]))
            updated = True
    if updated:
        save_expenses(expenses)
    return updated


def delete_expense(expense_id):
    expenses = [expense for expense in load_expenses() if expense["id"] != expense_id]
    save_expenses(expenses)
    return True
