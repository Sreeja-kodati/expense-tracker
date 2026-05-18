from fastapi import FastAPI, UploadFile
import json
from receipt_parser import parse_receipt
from database import *

app = FastAPI()

@app.post("/upload-receipt/")
async def upload_receipt(file: UploadFile):

    path = file.filename

    with open(path,"wb") as f:
        f.write(await file.read())

    result = parse_receipt(path)
    expenses = json.loads(result)

    saved=[]

    for exp in expenses:
        saved.append(create_expense(exp))

    return saved


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