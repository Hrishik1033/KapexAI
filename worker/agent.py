# ============================================================================
#  OLD ORCHESTRATOR (single-node research pipeline)
#  Kept commented out for reference; can be restored later if needed.
# ============================================================================
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from dotenv import load_dotenv
# load_dotenv()
# from langgraph.graph import END, START, StateGraph
# from langgraph.graph.state import CompiledStateGraph
# from pydantic import BaseModel, Field
#
# from worker.helpers.generate_answer import generate_answer
# from worker.helpers.search_tavily import search_tavily
# from worker.helpers.query_generator import generate_queries
#
#
# class State(BaseModel):
#     message: str = Field(default="", description="The user's input message")
#     queries: list[str] = Field(default_factory=list, description="Generated search queries")
#     web_scrape_result: str = Field(default="", description="Aggregated search results")
#     response: str = Field(default="", description="Final generated answer")
#
#
# def orchestrator(state: State) -> State:
#     queries = generate_queries(state.message)
#     state.queries = queries
#
#     all_results: list[str] = []
#     with ThreadPoolExecutor(max_workers=len(queries)) as executor:
#         futures = {executor.submit(search_tavily, q): q for q in queries}
#         for future in as_completed(futures):
#             all_results.append(future.result())
#
#     state.web_scrape_result = "\n\n---\n\n".join(all_results)
#     state.response = generate_answer(state.message, state.web_scrape_result)
#     return state
#
#
# def build_graph() -> CompiledStateGraph:
#     graph = StateGraph(State)
#     graph.add_node("orchestrator", orchestrator)
#     graph.add_edge(START, "orchestrator")
#     graph.add_edge("orchestrator", END)
#     return graph.compile()
#
#
# def run_cli():
#     graph = build_graph()
#
#     print("Agent ready. Type 'quit' to exit.\n")
#     while True:
#         user_input = input("You: ")
#         if user_input.strip().lower() in ("quit", "exit", "q"):
#             break
#
#         result = graph.invoke(State(message=user_input))
#         print(f"Agent: {result['response']}\n")
#
#
# if __name__ == "__main__":
#     run_cli()

# ============================================================================
#  NEW ORCHESTRATOR — linear flow of 4 agents:
#     questionnaire -> research -> report -> guardrail
# ============================================================================
from dotenv import load_dotenv

load_dotenv()
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from worker.agents.guardrail_agent import GuardrailAgent
from worker.agents.questionnaire_agent import QuestionnaireAgent
from worker.agents.report_agent import ReportAgent
from worker.agents.research_agent import ResearchAgent


class State(BaseModel):
    business_about: str = Field(default="", description="User's short description of the business")
    business_location: str = Field(default="", description="User's desired business location")
    business_vision: str = Field(default="", description="User's business vision / target scale and population")
    research_result: str = Field(default="", description="Research gathered by the research agent")
    report: str = Field(default="", description="Structured professional report")
    guardrail: dict[str, str] = Field(default_factory=dict, description="Guardrail agent output")


questionnaire_agent = QuestionnaireAgent()
research_agent = ResearchAgent()
report_agent = ReportAgent()
guardrail_agent = GuardrailAgent()


def orchestrator(state: State) -> State:
    answers = questionnaire_agent.ask()
    state.business_about = answers["business_about"]
    state.business_location = answers["business_location"]
    state.business_vision = answers["business_vision"]

    result = research_agent.run(answers)
    state.research_result = result

    state.report = report_agent.run(result)

    state.guardrail = guardrail_agent.run(state.report)
    return state


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(State)
    graph.add_node("orchestrator", orchestrator)
    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", END)
    return graph.compile()


def run_cli():
    graph = build_graph()

    print("Agent ready. Type 'quit' at any prompt to exit.\n")
    result = graph.invoke(State())
    print("\n" + "=" * 60)
    print("STRUCTURED REPORT")
    print("=" * 60)
    print(result["report"])
    print("=" * 60)
    print("Guardrail:", result["guardrail"]["message"])


if __name__ == "__main__":
    run_cli()
