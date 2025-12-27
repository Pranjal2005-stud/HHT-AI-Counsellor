POSITIVE = {"yes", "y", "yeah", "done", "implemented"}
NEGATIVE = {"no", "nope", "never"}


def classify_answer(answer: str) -> str:
    a = answer.lower().strip()
    if a in POSITIVE:
        return "YES"
    if a in NEGATIVE:
        return "NO"
    return "UNKNOWN"


def update_score(state, answer, weight):
    if classify_answer(answer) == "YES":
        state.score += weight


def should_repeat(answer: str) -> bool:
    return classify_answer(answer) == "UNKNOWN"
