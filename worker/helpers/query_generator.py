import json

from langchain_mistralai import ChatMistralAI

from worker.prompts import QUERY_GENERATOR_TEMPLATE


def generate_queries(message: str) -> list[str]:
    llm = ChatMistralAI(model="mistral-small-2506", temperature=0)
    chain = QUERY_GENERATOR_TEMPLATE | llm
    result = chain.invoke({"message": message})

    raw = result.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    queries = json.loads(raw)
    if not isinstance(queries, list) or not all(isinstance(q, str) for q in queries):
        raise ValueError(f"Expected a JSON array of strings, got: {raw}")
    return queries
