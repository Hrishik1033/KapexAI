from worker.prompts.questionnaire import QUESTIONS


class QuestionnaireAgent:
    def __init__(self) -> None:
        self.answers: dict[str, str] = {}

    def ask(self) -> dict[str, str]:
        print("\n--- Business Questionnaire ---")
        for key, question in QUESTIONS:
            print(f"\nQ: {question}")
            answer = input("A: ").strip()
            if answer.lower() in ("quit", "exit", "q"):
                raise SystemExit("Exited.")
            while not answer:
                print("Please provide an answer.")
                answer = input("A: ").strip()
            self.answers[key] = answer
        return self.answers
