from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from worker.helpers.generate_answer import generate_answer
from worker.helpers.search_tavily import search_tavily
from worker.helpers.query_generator import generate_queries


class State(BaseModel):
    message: str = Field(default="", description="The user's input message")
    queries: list[str] = Field(default_factory=list, description="Generated search queries")
    web_scrape_result: str = Field(default="", description="Aggregated search results")
    response: str = Field(default="", description="Final generated answer")


def orchestrator(state: State) -> State:
    queries = generate_queries(state.message)
    state.queries = queries

    all_results: list[str] = []
    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        futures = {executor.submit(search_tavily, q): q for q in queries}
        for future in as_completed(futures):
            all_results.append(future.result())

    state.web_scrape_result = "\n\n---\n\n".join(all_results)
    state.response = generate_answer(state.message, state.web_scrape_result)
    return state


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(State)
    graph.add_node("orchestrator", orchestrator)
    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", END)
    return graph.compile()

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