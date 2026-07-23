from typing import Literal
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field  
# --- State ------------------------------------------------------------------

class State(BaseModel):
    message: str = Field(default="", description="The user's input message")
    web_scrape_result: str = Field(default="", description="Raw results from the web search tool")
    response: str = Field(default="", description="Final generated answer from the LLM")

# --- Tools ------------------------------------------------------------------

tavily_tool = TavilySearchResults(max_results=2)

# --- Worker -----------------------------------------------------------------

def search_worker(query: str) -> str:
    """Single worker: runs a Tavily search and returns formatted results."""
    results = tavily_tool.invoke(query)
    return "\n\n".join(
        f"[{r.get('title', 'No title')}]\n{r.get('content', '')}" for r in results
    )

# --- Nodes ------------------------------------------------------------------

def orchestrator(state: State) -> State:
    """Decide how many workers are needed, fan out searches in parallel, gather results."""
    queries = _plan_queries(state.message)

    all_results: list[str] = []
    with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
        futures = {executor.submit(search_worker, q): q for q in queries}
        for future in as_completed(futures):
            all_results.append(future.result())

    state.web_scrape_result = "\n\n---\n\n".join(all_results)
    state.response = _generate_answer(state.message, state.web_scrape_result)
    return state

# --- Prompt -----------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior business strategy consultant at a top-tier management consulting firm (McKinsey, BCG, Bain caliber).

When a user describes a business idea or asks a business question, you respond with a structured, \
actionable analysis. Follow this framework:

1. **Executive Summary** — One sharp paragraph capturing the core opportunity or challenge.

2. **Market Landscape** — Size, trends, demand signals, key players. Use web search data when available.

3. **Business Model Options** — 2–3 viable models the user could pursue (e.g., D2C, wholesale, franchise, \
export). For each, state the value proposition, revenue model, and key risks.

4. **Go-to-Market Strategy** — Recommended first steps: target customer segments, channels, \
pricing positioning, and initial geographic focus.

5. **Operational Considerations** — Supply chain, sourcing, logistics, regulatory/licensing, \
and team requirements relevant to the business.

6. **Financial Outlook** — Rough cost structure, break-even timeline, and funding options. \
Use concrete numbers where data is available.

7. **Risks & Mitigations** — Top 3 risks with a one-line mitigation for each.

8. **Next Steps** — A prioritized list of 3–5 actions the user should take this week.

Be specific, data-driven, and concise. Avoid fluff. If data is unavailable, say so clearly. \
Write in a professional but accessible tone."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Here is the user's request:\n\n{message}\n\n---\nHere is research data gathered from the web:\n\n{context}"),
])

# --- Helpers ----------------------------------------------------------------

def _plan_queries(user_message: str) -> list[str]:
    """Decompose a business query into parallel research sub-queries."""
    keywords = [
        f"{user_message} market size trends 2025",
        f"{user_message} competitors landscape",
        f"{user_message} business model revenue strategy",
        f"{user_message} risks challenges",
    ]
    return keywords

def _generate_answer(message: str, context: str) -> str:
    """Pass gathered context + original message to the LLM via the prompt template."""
    from langchain_mistralai import ChatMistralAI

    llm = ChatMistralAI(model="mistral-small-2506", temperature=0)
    chain = prompt | llm

    result = chain.invoke({"message": message, "context": context})
    return result.content

# --- Graph ------------------------------------------------------------------

def build_graph() -> CompiledStateGraph:
    graph = StateGraph(State)

    graph.add_node("orchestrator", orchestrator)

    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", END)

    return graph.compile()

# --- CLI --------------------------------------------------------------------

if __name__ == "__main__":
    graph = build_graph()

    print("Agent ready. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("quit", "exit", "q"):
            break

        result = graph.invoke(State(message=user_input))
        print(f"Agent: {result['response']}\n")
