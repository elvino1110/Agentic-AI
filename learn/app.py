from supervisor import setup
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()
graph = None  # placeholder global

@app.on_event("startup")
async def startup_event():
    global graph
    graph = await setup()

class Question(BaseModel):
    question: str

@app.post("/invoke")
async def invoke_endpoint(payload: Question):
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": payload.question}]}
    )
    return result["messages"][-1].content