from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from worker.agents.guardrail_agent import GuardrailAgent
from worker.agents.questionnaire_agent import QuestionnaireAgent
from worker.agents.report_agent import ReportAgent
from worker.agents.research_agent import ResearchAgent


class State(BaseModel):
    user_name: str = Field(default="", description="User's name")
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
    state.user_name = answers["user_name"]
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
