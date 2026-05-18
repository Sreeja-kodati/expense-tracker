# AI Expense Tracker

A Streamlit dashboard that uses Google GenAI Gemini Vision to extract expenses from receipt images and store them in a local JSON database.

## Features

- Receipt upload with AI extraction
- Structured expense JSON output: `item`, `price`, `category`, `date`
- CRUD operations in a Streamlit dashboard
- Editable expense table
- Delete expenses
- Monthly insights, category pie chart, spending trend line chart
- AI-powered expense summarization
- Budget warning display

## Files

- `app.py` - Streamlit application UI
- `receipt_ai.py` - Gemini Vision receipt parser + AI summarization
- `database.py` - JSON CRUD storage with UUID support
- `analytics.py` - Plotly analytics and spending calculations
- `expenses.json` - local data store
- `requirements.txt` - Python dependencies

## Installation

1. Activate your Python environment:

```powershell
cd "c:\expense tracker"
python -m venv venv
venv\Scripts\activate
```

2. Install project dependencies:

```powershell
pip install -r requirements.txt
```

3. Ensure `GOOGLE_API_KEY` is set in your environment:

```powershell
$env:GOOGLE_API_KEY = "YOUR_API_KEY"
```

## Run

```powershell
streamlit run app.py
```

## Notes

- The app stores expenses in `expenses.json` automatically.
- If `GOOGLE_API_KEY` is not set, AI receipt extraction and Gemini summary are disabled, but manual expense entry and analytics still work.
- Use a clear receipt image for the best AI extraction results when a key is available.
