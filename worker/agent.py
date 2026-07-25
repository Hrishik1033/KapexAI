from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from worker.helpers import search_tavily, plan_queries
from worker.prompts import prompt

# --- State ------------------------------------------------------------------

class State(BaseModel):
    message: str = Field(default="", description="The user's input message")
    web_scrape_result: str = Field(default="", description="Raw results from the web search tool")
    response: str = Field(default="", description="Final generated answer from the LLM")

# --- Nodes ------------------------------------------------------------------

def orchestrator(state: State) -> State:
    """Dynamically plan queries based on task complexity, fan out searches in parallel."""
    queries = plan_queries(state.message)

    all_results: list[str] = []
    with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
        futures = {executor.submit(search_tavily, q): q for q in queries}
        for future in as_completed(futures):
            all_results.append(future.result())

    state.web_scrape_result = "\n\n---\n\n".join(all_results)
    state.response = _generate_answer(state.message, state.web_scrape_result)
    return state

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

def run_cli():
    graph = build_graph()

    print("Agent ready. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("quit", "exit", "q"):
            break

        result = graph.invoke(State(message=user_input))
        print(f"Agent: {result['response']}\n")


if __name__ == "__main__":
    run_cli()
