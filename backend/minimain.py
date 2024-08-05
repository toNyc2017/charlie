from fastapi import FastAPI

#dummy change to trigger re deployment

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

