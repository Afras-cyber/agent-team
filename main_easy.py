from fastapi import FastAPI
from pydantic import BaseModel
from team_easy_v3 import graph

app = FastAPI(title="Easy Agent Team")

class TeamRequest(BaseModel):
    topic: str

@app.get("/")
def home():
    return {"message": "Easy Team is running. Go to /docs"}

@app.post("/team")
def run_team(req: TeamRequest):
    result = graph.invoke({
        "topic": req.topic,
        "attempts": 0,
        "feedback": "",
        "approved": False
    })
    return {
        "final_invitation": result['invitation'],
        "attempts": result['attempts']
    }