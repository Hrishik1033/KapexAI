from langchain_community.tools.tavily_search import TavilySearchResults

tavily_tool = TavilySearchResults(max_results=2)
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

def search_tavily(query: str) -> str:
    results = tavily_tool.invoke(query)
    return "\n\n".join(
        f"[{r.get('title', 'No title')}]\n{r.get('content', '')}"
        for r in results
    )
