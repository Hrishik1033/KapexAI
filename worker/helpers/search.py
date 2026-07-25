from langchain_community.tools.tavily_search import TavilySearchResults

tavily_tool = TavilySearchResults(max_results=2)


def search_tavily(query: str) -> str:
    """Search Tavily for information. Returns formatted results."""
    results = tavily_tool.invoke(query)
    if not results:
        return ""
    return "\n\n".join(
        f"[{r.get('title', 'No title')}]\n{r.get('content', '')}" for r in results
    )
