from datetime import datetime
import pandas as pd
import plotly.express as px


def _expenses_dataframe(expenses):
    if not expenses:
        df = pd.DataFrame(columns=["id", "item", "price", "category", "date"])
        df["price"] = pd.Series(dtype="float64")
        df["category"] = pd.Series(dtype="string")
        df["item"] = pd.Series(dtype="string")
        df["date"] = pd.to_datetime(pd.Series([], dtype="string"), errors="coerce")
        df["month"] = pd.Series(dtype="string")
        return df

    df = pd.DataFrame(expenses)
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    else:
        df["price"] = 0.0
    if "category" not in df.columns:
        df["category"] = "Other"
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        df["date"] = pd.NaT

    df["category"] = df["category"].fillna("Other")
    df["item"] = df["item"].fillna("Untitled")
    df["month"] = df["date"].dt.strftime("%Y-%m").fillna("Unknown")
    return df


def total_spending(expenses):
    df = _expenses_dataframe(expenses)
    return float(df["price"].sum())


def current_month_spending(expenses):
    df = _expenses_dataframe(expenses)
    today = datetime.today()
    current_month = today.strftime("%Y-%m")
    return float(df[df["month"] == current_month]["price"].sum())


def transactions_count(expenses):
    return len(expenses or [])


def category_summary(expenses):
    df = _expenses_dataframe(expenses)
    grouped = df.groupby("category", as_index=False)["price"].sum().sort_values(by="price", ascending=False)
    return grouped


def monthly_summary(expenses):
    df = _expenses_dataframe(expenses)
    grouped = df.groupby("month", as_index=False)["price"].sum().sort_values(by="month")
    return grouped


def highest_spending_category(expenses):
    grouped = category_summary(expenses)
    if grouped.empty:
        return {"category": "None", "amount": 0.0}
    top = grouped.iloc[0]
    return {"category": top["category"], "amount": float(top["price"])}


def budget_warning(expenses, budget=1000.0):
    monthly = current_month_spending(expenses)
    if monthly >= budget:
        return f"Warning: your current month spending is ${monthly:,.2f}, which exceeds your budget of ${budget:,.2f}."
    if monthly >= budget * 0.8:
        return f"Caution: your spending is approaching budget at ${monthly:,.2f}."
    return "Your spending is within budget."


def create_pie_chart(expenses):
    grouped = category_summary(expenses)
    if grouped.empty:
        return px.pie(values=[1], names=["No data"], title="Category Spending")
    return px.pie(grouped, names="category", values="price", title="Spending by Category", hole=0.5)


def create_bar_chart(expenses):
    grouped = monthly_summary(expenses)
    if grouped.empty:
        return px.bar(x=["No data"], y=[0], title="Monthly Expenses")
    return px.bar(grouped, x="month", y="price", title="Monthly Spending", labels={"month": "Month", "price": "Spend ($)"})


def create_line_chart(expenses):
    grouped = monthly_summary(expenses)
    if grouped.empty:
        return px.line(x=["No data"], y=[0], title="Spending Trend")
    return px.line(grouped, x="month", y="price", title="Spending Trend", markers=True, labels={"month": "Month", "price": "Spend ($)"})
