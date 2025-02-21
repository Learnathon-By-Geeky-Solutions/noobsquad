#importing fastapi
from fastapi import FastAPI
from typing import Optional

#creating an instances
app = FastAPI()

@app.get("/")
def root():
    return "This is just demo main page"