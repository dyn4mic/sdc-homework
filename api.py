import uvicorn
from fastapi import FastAPI, UploadFile, File,HTTPException
from fastapi.responses import StreamingResponse
from datetime import timedelta,date
from typing import Union
from pydantic import BaseModel

app = FastAPI()


class Magic(BaseModel):
    pow2: int

class ShifDateModel(BaseModel):
    startDate: date

@app.get("/")
def root():
    return {"hello fhtw course!"}

@app.post("/domagicwithnumber",response_model=Magic)
def doMagic(number: int):
    return {"pow2":number**2}

@app.post("/shiftDate", response_model=ShifDateModel)
def shiftDate(endDate: Union[date,None],shiftdays: int):
    return {"startDate":endDate-timedelta(days=shiftdays)}


def start():
    uvicorn.run("api:app", host="0.0.0.0",reload=False)

if __name__ == '__main__':
    start()