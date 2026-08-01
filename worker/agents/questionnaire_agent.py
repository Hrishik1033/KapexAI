from worker.prompts.questionnaire import QUESTIONS

NAME_PROMPT = "What is your name?"


class QuestionnaireAgent:
    def __init__(self) -> None:
        self.answers: dict[str, str] = {}

    def ask(self) -> dict[str, str]:
        print("\n--- Business Questionnaire ---")
        prompts = [("user_name", NAME_PROMPT)] + QUESTIONS
        for key, question in prompts:
            print(f"\nQ: {question}")
            answer = self._prompt("A")
            self.answers[key] = answer
        return self.answers

    @staticmethod
    def _prompt(label: str) -> str:
        answer = input(f"{label}: ").strip()
        if answer.lower() in ("quit", "exit", "q"):
            raise SystemExit("Exited.")
        while not answer:
            print("Please provide an answer.")
            answer = input(f"{label}: ").strip()
        return answer
