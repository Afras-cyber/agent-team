from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
import requests
import urllib.parse

llm = ChatOllama(model="llama3.2:3b", temperature=0)

class Notebook(TypedDict):
    topic: str
    plan: str
    research: str
    invitation: str
    feedback: str
    approved: bool
    attempts: int

def planner(state: Notebook):
    print("\n--- PLANNER is working ---")
    prompt = f"Make a very short 3-point plan for: {state['topic']}"
    result = llm.invoke(prompt)
    return {"plan": result.content}

def researcher(state: Notebook):
    print("\n--- RESEARCHER is searching ---")
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote('Popcorn')}"
        r = requests.get(url, timeout=10, headers={"User-Agent": "easy-team"})
        research = r.json().get("extract", "No info")[:500]
    except Exception as e:
        research = f"Search failed: {e}"
    print("Research done:", research[:100])
    return {"research": research}

def writer(state: Notebook):
    attempts = state.get("attempts", 0) + 1
    print(f"\n--- WRITER is writing, attempt {attempts} ---")
    feedback = state.get("feedback", "")
    prompt = f"""Write a short fun invitation for: {state['topic']}
Plan: {state['plan']}
Facts: {state['research']}
Teacher feedback: {feedback}
RULE: Max 6 sentences only."""
    result = llm.invoke(prompt)
    return {"invitation": result.content, "attempts": attempts}

def critic(state: Notebook):
    print("\n--- CRITIC is checking ---")
    text = state['invitation']
    sentences = text.count('.') + text.count('!')
    has_popcorn = "popcorn" in text.lower()
    print(f"Critic counted {sentences} sentences, has popcorn? {has_popcorn}")
    if sentences <= 6 and has_popcorn:
        print("Critic says: APPROVED")
        return {"approved": True, "feedback": ""}
    else:
        print("Critic says: NEEDS FIX - must be 6 sentences max AND must include popcorn")
        return {"approved": False, "feedback": "Too long or missing popcorn! Make it max 6 sentences and MUST include the word popcorn."}

def route_after_critic(state: Notebook):
    if state['approved']:
        return "approved"
    else:
        return "needs_fix"

builder = StateGraph(Notebook)
builder.add_node("planner", planner)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)
builder.add_node("critic", critic)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", "critic")
builder.add_conditional_edges("critic", route_after_critic, {
    "approved": END,
    "needs_fix": "writer"
})

graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"topic": "Movie night for 5 friends, Friday, at home, horror movie", "attempts": 0, "feedback": "", "approved": False})
    print("\n===== FINAL INVITATION =====")
    print(result['invitation'])
    print(f"\nAttempts used: {result['attempts']}")