from services import generate_comprehensive_synopsis
idea = "AI-powered chatbot"
repos = ["repo1 💻 Python", "repo2 💻 Java"]
research_data = "Some research data"
discussion_history = ["Discussion 1", "Discussion 2"]
path = generate_comprehensive_synopsis(idea, repos, research_data, discussion_history)
print(f"Synopsis generated at: {path}")