from typing import TypedDict
from langchain_ollama import ChatOllama
import requests
from langgraph.graph import StateGraph, START, END


llm = ChatOllama(model="llama3.2:3b")

class Notebook(TypedDict):
    topic: str
    plan: str
    research: str
    invitation: str

def planner(state: Notebook):
    print("---PLANNER---")
    prompt = f"Make a very short 3-point plan for : {state['topic']}"
    result = llm.invoke(prompt)
    print(result.content)
    return {"plan": result.content}

def researcher(state: Notebook):
    print("---RESEARCHER---")
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{state['topic']}"
        
        r = requests.get(
            url, 
            timeout=10, 
            headers={"User-Agent": "AgentTeam/1.0"})
        
        research = r.json().get("extract","No info")[:500]
    except:
        research = "No research found"
    return {"research": research}

def writer(state: Notebook):
    print("---WRITER---")
    prompt = f"Write a short blog post about {state['topic']} using the plan {state['plan']} and research {state['research']}"
    result = llm.invoke(prompt)
    print(result.content)
    return {"invitation": result.content}

builder = StateGraph(Notebook);
builder.add_node("planner", planner);
builder.add_node("researcher", researcher);
builder.add_node("writer", writer);

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", END)

graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"topic": "Birthday party for my friend Afraz, 20 people, at home"})
    print("\n===== FINAL INVITATION =====")
    print(result['invitation'])
    print("\n===== WHAT IS IN THE NOTEBOOK? =====")
    print("Plan:", result['plan'][:200])
    print("Research:", result['research'][:200])