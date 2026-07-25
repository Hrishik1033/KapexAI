import json

from worker.prompts import plan_prompt


def plan_queries(user_message: str) -> list[str]:
    """Use the LLM to dynamically decide how many sub-queries to generate."""
    from langchain_mistralai import ChatMistralAI

    llm = ChatMistralAI(model="mistral-small-2506", temperature=0)
    chain = plan_prompt | llm

    result = chain.invoke({"message": user_message})
    raw = result.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()

    queries = json.loads(raw)
    if not isinstance(queries, list) or not queries:
        return [user_message]
    return queries
