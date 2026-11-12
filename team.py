# 1. Tools
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults

llm = ChatOllama(model="llama3.2:3b", temperature=0)
search = DuckDuckGoSearchResults(num_results=2)


# 2. The shared notebook. Every worker can read and write here.
class TeamState(TypedDict):
    topic: str
    plan: str
    research: str
    draft: str
    feedback: str
    approved: bool
    attempts: int

# 3. Worker 1: Planner
def planner(state: TeamState):
    print("\n--- PLANNER is working ---")
    prompt = f"Make a short 3-point plan to explain this topic: {state['topic']}. Return only the plan."
    result = llm.invoke(prompt)
    return {"plan": result.content}

# 4. Worker 2: Researcher
import requests
import urllib.parse

def researcher(state: TeamState):
    print("\n--- RESEARCHER is searching ---")
    try:
        # Clean the topic: "What is LangGraph?" -> "LangGraph"
        topic_clean = state['topic'].replace("What is ", "").replace("?", "").strip()
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic_clean)}"
        r = requests.get(url, timeout=10, headers={"User-Agent": "agent-team-learning"})
        if r.status_code == 200:
            data = r.json()
            research = data.get("extract", "No summary found")
        else:
            research = "Wikipedia had no page, use general knowledge"
    except Exception as e:
        # Even if internet fails, don't crash the whole team
        research = f"Search failed: {e}. Use general knowledge about {state['topic']}"

    print("Research found:", research[:200])
    return {"research": research}

# 5. Worker 3: Writer
def writer(state: TeamState):
    print(f"\n--- WRITER is writing, attempt {state.get('attempts', 0) + 1} ---")
    prompt = f"""Write a short explanation for: {state['topic']}
Use this plan:
{state.get('plan', '')}
Use these facts:
{state.get('research', '')}
Feedback from last time, fix it if there is any:
{state.get('feedback', 'No feedback yet')}
Keep it to 5 sentences."""
    result = llm.invoke(prompt)
    return {"draft": result.content, "attempts": state.get('attempts', 0) + 1}

# 6. Worker 4: Critic
def critic(state: TeamState):
    print("\n--- CRITIC is checking ---")
    prompt = f"""Check this draft for topic: {state['topic']}
Draft: {state['draft']}
If it is clear and covers the topic, reply with ONLY the word APPROVED.
If it is missing facts or unclear, reply with NEEDS FIX and one short sentence why."""
    result = llm.invoke(prompt)
    text = result.content
    print("Critic says:", text)
    if "APPROVED" in text.upper():
        return {"approved": True, "feedback": ""}
    else:
        return {"approved": False, "feedback": text}

# 7. The fork in the road
def should_retry(state: TeamState):
    if state.get('approved') or state.get('attempts', 0) >= 2:
        return END
    return "writer"

# 8. Build the flowchart
builder = StateGraph(TeamState)
builder.add_node("planner", planner)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)
builder.add_node("critic", critic)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", "critic")
builder.add_conditional_edges("critic", should_retry, {"writer": "writer", END: END})

graph = builder.compile()

# 9. Run it
if __name__ == "__main__":
    result = graph.invoke({"topic": "What is LangGraph?", "attempts": 0, "feedback": ""})
    print("\n===== FINAL ANSWER =====")
    print(result['draft'])
    print("\nAttempts:", result['attempts'])