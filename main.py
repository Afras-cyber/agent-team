from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
from team import graph

app = FastAPI()

class TeamRequest(BaseModel):
    topic: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/team")
def team(req: TeamRequest):
    result = graph.invoke({"topic":req.topic,"attempts":0,"feedback":""})
    return {
        "topic": req.topic,
        "final_answer": result["draft"],
        "attempts": result["attempts"],
        "approved": result["approved"]
    }

# Streaming version - show each worker live
@app.post("/team/stream")
async def run_team_stream(req: TeamRequest):
    async def generate():
        async for chunk in graph.astream(
            {"topic": req.topic, "attempts": 0, "feedback": ""},
            stream_mode="updates"
        ):
            # chunk looks like {"planner": {...}} or {"writer": {...}}
            for worker_name in chunk:
                yield f"data: {json.dumps({'worker': worker_name, 'output': str(chunk[worker_name])[:500]})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
