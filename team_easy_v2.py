from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
import requests
import urllib.parse

llm = ChatOllama(model="llama3.2:3b", temperature=0)

# Notebook now has 3 new pages: feedback, approved, attempts
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
        # FIX: Use "Birthday" not "Birthday party" - this page has info
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote('Birthday')}"
        r = requests.get(url, timeout=10, headers={"User-Agent": "easy-team"})
        research = r.json().get("extract", "No info")[:500]
    except Exception as e:
        research = f"Search failed, use general knowledge. Error: {e}"
    print("Research done:", research[:100])
    return {"research": research}

def writer(state: Notebook):
    # Count how many times Writer has tried
    attempts = state.get("attempts", 0) + 1
    print(f"\n--- WRITER is writing, attempt {attempts} ---")
    feedback = state.get("feedback", "")
    prompt = f"""
    Write a short fun birthday invitation for: {state['topic']}
    Plan: {state['plan']}
    Facts: {state['research']}
    Teacher feedback from last time: {feedback}
    RULE: Max 6 sentences only. Short and fun."""
    result = llm.invoke(prompt)
    return {"invitation": result.content, "attempts": attempts}

def critic(state: Notebook):
    print("\n--- CRITIC is checking ---")
    # Count sentences by counting dots
    sentences = state['invitation'].count('.') + state['invitation'].count('!')
    print(f"Critic counted {sentences} sentences")
    if sentences <= 8:
        print("Critic says: APPROVED")
        return {"approved": True, "feedback": ""}
    else:
        print("Critic says: NEEDS FIX - too long, make it shorter")
        return {"approved": False, "feedback": "Too long! Make it max 6 sentences, delete the extra sections."}

# The traffic light: where to go after Critic?
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
# This is the fork! Critic decides where to go
builder.add_conditional_edges("critic", route_after_critic, {
    "approved": END,
    "needs_fix": "writer"
})

graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"topic": "Birthday party for my friend Afraz, 20 people, at home", "attempts": 0, "feedback": "", "approved": False})
    print("\n===== FINAL INVITATION =====")
    print(result['invitation'])
    print(f"\nAttempts used: {result['attempts']}")