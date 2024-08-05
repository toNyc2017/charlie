from fastapi import FastAPI

#dummy change to trigger re deployment
#another dummy change to trigger

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

