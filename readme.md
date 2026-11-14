# Agent Team - Easy Version
Planner + Researcher + Writer + Critic working together with LangGraph

How it works:
Planner makes a plan -> Researcher finds facts on Wikipedia -> Writer writes invitation -> Critic checks length + keyword -> If NEEDS FIX, back to Writer

Run:
uvicorn main_easy:app --reload --port 8002
Docs: http://127.0.0.1:8002/docs

Example:
Topic: "Movie night for 5 friends, Friday, at home, horror movie"
Result: Final invitation + attempts used