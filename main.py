from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import tempfile
from receipt_parser import parse_receipt
from database import *

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Expense Tracker API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/upload-receipt/")
async def upload_receipt(file: UploadFile):
    try:
        # Use temporary directory for file storage on Vercel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = parse_receipt(tmp_path)
        expenses = json.loads(result)

        saved=[]

        for exp in expenses:
            saved.append(create_expense(exp))

        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass

        return saved
    except Exception as e:
        raise ValueError(f"Error processing receipt: {str(e)}")


@app.get("/expenses/")
def read_expenses():
    return get_expenses()


@app.put("/expenses/{expense_id}")
def update(expense_id:str,data:dict):
    update_expense(expense_id,data)
    return {"message":"updated"}


@app.delete("/expenses/{expense_id}")
def delete(expense_id:str):
    delete_expense(expense_id)
    return {"message":"deleted"}