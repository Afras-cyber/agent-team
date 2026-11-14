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
    final_plan: str
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
        # YOUR CHANGE: Search for "Study skills" instead of Popcorn
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote('Study skills')}"
        r = requests.get(url, timeout=10, headers={"User-Agent": "my-team"})
        research = r.json().get("extract", "No info")[:500]
    except Exception as e:
        research = f"Search failed: {e}"
    return {"research": research}

def writer(state: Notebook):
    attempts = state.get("attempts", 0) + 1
    print(f"\n--- WRITER is writing, attempt {attempts} ---")
    feedback = state.get("feedback", "")
    prompt = f"""Write a short study plan for: {state['topic']}
Plan: {state['plan']}
Facts: {state['research']}
Teacher feedback: {feedback}
RULE: Max 6 sentences only, MUST include the word 'break'."""
    result = llm.invoke(prompt)
    return {"final_plan": result.content, "attempts": attempts}

def critic(state: Notebook):
    print("\n--- CRITIC is checking ---")
    text = state['final_plan']
    sentences = text.count('.') + text.count('!')
    has_break = "break" in text.lower()
    print(f"Critic counted {sentences} sentences, has break? {has_break}")
    # YOUR RULE: same as Movie Night, but word is "break" not "popcorn"
    if sentences <= 6 and has_break:
        print("Critic says: APPROVED")
        return {"approved": True, "feedback": ""}
    else:
        print("Critic says: NEEDS FIX")
        return {"approved": False, "feedback": "Must be 6 sentences max and MUST include word break."}

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
    # YOUR CHANGE: Put your own topic here
    result = graph.invoke({
        "topic": "Study plan for my exams, 7 days, 3 subjects, 2 hours per day",
        "attempts": 0,
        "feedback": "",
        "approved": False
    })
    print("\n===== FINAL STUDY PLAN =====")
    print(result['final_plan'])
    print(f"\nAttempts used: {result['attempts']}")