from langchain_mistralai import ChatMistralAI

from worker.prompts import ANSWER_TEMPLATE


def generate_answer(message: str, context: str) -> str:
    llm = ChatMistralAI(model="mistral-small-2506", temperature=0)
    chain = ANSWER_TEMPLATE | llm
    result = chain.invoke({"message": message, "context": context})
    return result.content
