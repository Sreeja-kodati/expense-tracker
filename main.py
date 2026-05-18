from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import tempfile
import traceback
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
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON from receipt parser: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/expenses/")
def read_expenses():
    try:
        return get_expenses()
    except Exception as e:
        print(f"Error reading expenses: {e}")
        return []


@app.put("/expenses/{expense_id}")
def update(expense_id:str, data:dict):
    try:
        update_expense(expense_id, data)
        return {"message": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@app.delete("/expenses/{expense_id}")
def delete(expense_id:str):
    try:
        delete_expense(expense_id)
        return {"message": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")