import io
import json
import os
import re
from datetime import datetime
from PIL import Image
from google import genai

CATEGORY_KEYWORDS = {
    "Food": ["restaurant", "cafe", "coffee", "burger", "pizza", "meal", "dinner", "lunch", "breakfast", "snack"],
    "Groceries": ["grocery", "supermarket", "market", "produce", "vegetable", "fruit", "dairy", "bread", "shopping"],
    "Transportation": ["taxi", "uber", "lyft", "bus", "train", "metro", "flight", "transport", "gas", "fuel"],
    "Utilities": ["electricity", "water", "internet", "phone", "utility", "gas bill", "rent"],
    "Health": ["pharmacy", "drugstore", "medical", "doctor", "clinic", "hospital", "health"],
    "Entertainment": ["movie", "ticket", "concert", "theater", "netflix", "spotify", "game"],
    "Travel": ["hotel", "airbnb", "flight", "car rental", "taxi", "train"],
    "Office": ["stationery", "office", "printer", "supplies", "software", "hardware"],
    "Other": []
}


def _normalize_price(value):
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return 0.0

    cleaned = value.replace("$", "").replace("USD", "").replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
    return float(match.group(1)) if match else 0.0


def _normalize_date(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if not isinstance(value, str):
        return ""

    value = value.strip()
    patterns = [r"(\d{4}-\d{1,2}-\d{1,2})", r"(\d{1,2}/\d{1,2}/\d{2,4})", r"(\d{1,2}-\d{1,2}-\d{2,4})"]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            date_text = match.group(1)
            try:
                parsed = datetime.fromisoformat(date_text)
                return parsed.date().isoformat()
            except ValueError:
                for fmt in ["%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y"]:
                    try:
                        parsed = datetime.strptime(date_text, fmt)
                        return parsed.date().isoformat()
                    except ValueError:
                        continue
    return ""


def _categorize_item(text):
    text_value = str(text).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_value:
                return category
    return "Other"


def _extract_json(raw_text):
    if not raw_text:
        return []
    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\])", raw_text, re.S)
        if match:
            try:
                parsed = json.loads(match.group(1))
                return parsed
            except json.JSONDecodeError:
                pass
    return []


def _get_genai_client():
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("AI_GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Google API key not found. Please set the environment variable GOOGLE_API_KEY or AI_GOOGLE_API_KEY. "
            "Example: $env:GOOGLE_API_KEY='YOUR_KEY' in PowerShell."
        )
    return genai.Client(api_key=api_key)


def parse_receipt_image(image_bytes):
    """Send receipt image to Gemini Vision and return structured expense entries."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    prompt = (
        "Extract every line item from this receipt image. "
        "Return a JSON array of objects with keys: item, price, category, date. "
        "If the receipt contains a date, return it in ISO format (YYYY-MM-DD). "
        "If a category is missing, use a logical category name. "
        "Return ONLY valid JSON in the response."
    )

    client = _get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, image],
        temperature=0.0,
    )

    raw_text = getattr(response, "text", "") or ""
    expenses = _extract_json(raw_text)
    normalized = []

    for item in expenses:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "item": str(item.get("item", "Untitled")).strip() or "Untitled",
            "price": _normalize_price(item.get("price", "0")),
            "category": str(item.get("category", "")).strip() or _categorize_item(item.get("item", "")),
            "date": _normalize_date(item.get("date", "")) or "",
        })

    return normalized


def _local_summary(expenses):
    total = sum(float(exp.get("price", 0.0)) for exp in expenses)
    categories = {}
    months = {}
    for exp in expenses:
        categories[exp.get("category", "Other")] = categories.get(exp.get("category", "Other"), 0.0) + float(exp.get("price", 0.0))
        date = exp.get("date", "")
        month = date[:7] if date else "Unknown"
        months[month] = months.get(month, 0.0) + float(exp.get("price", 0.0))

    top_category = max(categories.items(), key=lambda x: x[1], default=("None", 0.0))
    return (
        f"Summary: {len(expenses)} transactions totaling ${total:,.2f}. "
        f"Top category is {top_category[0]} with ${top_category[1]:,.2f}. "
        f"Use a Google API key to enable Gemini-powered AI insights."
    )


def summarize_expenses(expenses):
    """Ask Gemini to summarize the expense dataset for dashboard insights."""
    if not expenses:
        return "No expense data available yet. Upload a receipt or add your first expense."

    payload = json.dumps([
        {"item": e["item"], "price": float(e["price"]), "category": e["category"], "date": e.get("date", "")} 
        for e in expenses
    ], indent=2)

    prompt = (
        "Review the following expense data and provide a short summary of spending patterns, "
        "major categories, and monthly insights. Return a concise paragraph. "
        "Do not return JSON."
    )

    try:
        client = _get_genai_client()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, payload],
            temperature=0.2,
        )
        return getattr(response, "text", "").strip() or "Expense summary is unavailable at the moment."
    except EnvironmentError:
        return _local_summary(expenses)
