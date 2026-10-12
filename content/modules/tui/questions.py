class TUIQuestions:
    PROCEED_QUESTION = "Proceed anyway?"

    @classmethod
    def complaints_proceed(cls, complaints: list[str]) -> str:
        complaints_str = "\n".join(complaints)
        return f"{complaints_str}\n{cls.PROCEED_QUESTION}"