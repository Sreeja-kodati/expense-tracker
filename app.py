import pandas as pd
import streamlit as st
from datetime import date
from receipt_ai import parse_receipt_image, summarize_expenses
from database import create_expense, delete_expense, get_expenses, update_expense
from analytics import (
    budget_warning,
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    current_month_spending,
    highest_spending_category,
    total_spending,
    transactions_count,
)

st.set_page_config(page_title="AI Expense Tracker", page_icon="💳", layout="wide")


def load_expense_data():
    return get_expenses()


def has_genai_api_key():
    import os
    return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("AI_GOOGLE_API_KEY"))


def show_metrics(expenses):
    total = total_spending(expenses)
    month = current_month_spending(expenses)
    count = transactions_count(expenses)
    top = highest_spending_category(expenses)
    warning_text = budget_warning(expenses)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Spending", f"${total:,.2f}")
    col2.metric("This Month", f"${month:,.2f}")
    col3.metric("Transactions", f"{count}")
    col4.metric("Top Category", top["category"])

    if warning_text:
        st.info(warning_text)


def display_expense_editor(expenses):
    if not expenses:
        st.info("No expenses found yet. Upload a receipt or add a new expense.")
        return

    df = pd.DataFrame(expenses)
    if df.empty:
        st.info("No structured expense records are available.")
        return

    df = df[["id", "item", "price", "category", "date"]]
    edited = st.data_editor(
        df,
        column_config={"id": st.ColumnConfig(type="text", disabled=True)},
        use_container_width=True,
        num_rows="dynamic",
        key="expense_editor",
    )

    if st.button("Save updates", key="save_updates"):
        records = edited.to_dict("records")
        saved = 0
        for row in records:
            expense_id = row.pop("id")
            existing = next((item for item in expenses if item["id"] == expense_id), None)
            if existing and (existing["item"] != row["item" ] or float(existing["price"]) != float(row["price"]) or existing["category"] != row["category"] or existing.get("date", "") != row["date"]):
                update_expense(expense_id, row)
                saved += 1
        if saved:
            st.success(f"Saved {saved} updated expense(s).")
        else:
            st.info("No changes detected.")

    delete_ids = st.multiselect(
        "Select expenses to delete",
        options=df["id"].tolist(),
        format_func=lambda x: next((f"{item['item']} — ${item['price']:.2f}" for item in expenses if item["id"] == x), x),
        key="delete_select",
    )

    if st.button("Delete selected", key="delete_selected") and delete_ids:
        for expense_id in delete_ids:
            delete_expense(expense_id)
        st.success(f"Deleted {len(delete_ids)} expense(s).")
        st.experimental_rerun()


st.title("AI Expense Tracker")
st.markdown("Modern dashboard for smart receipt extraction and expense analytics.")

page = st.sidebar.radio("Navigation", ["Dashboard", "Receipt Upload", "Manage Expenses", "Analytics"])

expenses = load_expense_data()

if page == "Dashboard":
    show_metrics(expenses)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Category Spending")
        st.plotly_chart(create_pie_chart(expenses), use_container_width=True)
    with col2:
        st.subheader("Monthly Spending")
        st.plotly_chart(create_bar_chart(expenses), use_container_width=True)

    st.markdown("---")
    st.subheader("Latest Expenses")
    latest_df = pd.DataFrame(expenses)
    if latest_df.empty:
        st.info("No expenses found yet.")
    else:
        latest_df = latest_df.reindex(columns=["item", "price", "category", "date"])
        if "date" in latest_df.columns:
            latest_df = latest_df.sort_values(by="date", ascending=False, na_position="last")
        st.dataframe(latest_df.head(10), use_container_width=True)

elif page == "Receipt Upload":
    st.subheader("Upload Receipt")
    st.markdown("Upload a receipt image and let Gemini Vision extract structured expenses automatically.")
    if not has_genai_api_key():
        st.warning("Google API key is not available. AI receipt extraction is disabled. Use manual entry below to add expenses.")

    uploaded = st.file_uploader("Receipt image", type=["png", "jpg", "jpeg"], accept_multiple_files=False)

    if uploaded is not None:
        if not has_genai_api_key():
            st.error("Cannot extract receipt without GOOGLE_API_KEY. Please set the key or use manual entry.")
            parsed = []
        else:
            try:
                with st.spinner("Extracting receipt data..."):
                    parsed = parse_receipt_image(uploaded.getvalue())
            except Exception as error:
                st.error(f"Receipt parsing failed: {error}")
                parsed = []

        if parsed:
            st.success("Receipt parsed successfully.")
            parsed_df = pd.DataFrame(parsed)
            st.dataframe(parsed_df, use_container_width=True)

            if st.button("Add parsed expenses to tracker"):
                for row in parsed:
                    create_expense(row)
                st.success("Parsed expenses added successfully.")
                st.experimental_rerun()
        else:
            if uploaded is not None and has_genai_api_key():
                st.warning("Receipt extraction did not return structured data. Check the image quality and try again.")

    st.markdown("---")
    st.subheader("Manual Expense Entry")
    with st.form("manual_expense_form", clear_on_submit=True):
        item = st.text_input("Item name")
        price = st.number_input("Amount", min_value=0.0, format="%.2f")
        category = st.text_input("Category", value="Other")
        expense_date = st.date_input("Date", value=date.today())
        submitted = st.form_submit_button("Add expense manually")
        if submitted:
            create_expense({
                "item": item or "Untitled",
                "price": price,
                "category": category.strip() or "Other",
                "date": expense_date.isoformat(),
            })
            st.success("Expense added successfully.")
            st.experimental_rerun()

elif page == "Manage Expenses":
    st.subheader("Manage Expenses")
    st.markdown("Edit existing expenses inline, then save updates or remove items.")
    display_expense_editor(expenses)

elif page == "Analytics":
    st.subheader("Analytics & Insights")
    show_metrics(expenses)
    st.markdown("### Spending Overview")
    st.plotly_chart(create_line_chart(expenses), use_container_width=True)
    st.plotly_chart(create_bar_chart(expenses), use_container_width=True)
    st.plotly_chart(create_pie_chart(expenses), use_container_width=True)

    st.markdown("### AI Expense Summary")
    try:
        st.write(summarize_expenses(expenses))
    except EnvironmentError as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"Unable to generate AI summary: {error}")
