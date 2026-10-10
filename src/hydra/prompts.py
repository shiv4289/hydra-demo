"""Prompts the broker itself sends to backends (judge, aggregator).

Real backends read them as instructions; mock backends recognise them by prefix.
"""

JUDGE_SYSTEM = (
    "You are a strict grader. Given a QUESTION and a candidate ANSWER, rate how "
    "completely and correctly the answer addresses the question. Reply with ONLY "
    "a number between 0 and 1."
)

AGGREGATOR_SYSTEM = (
    "You are an expert editor. You will receive a QUESTION and several DRAFT "
    "answers from different models. Write the single best final answer: keep what "
    "is correct, fix what is wrong, drop repetition. Do not mention the drafts."
)


def judge_messages(question: str, answer: str) -> list[dict]:
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": f"QUESTION:\n{question}\n\nANSWER:\n{answer}"},
    ]


def aggregator_messages(question: str, drafts: list[tuple[str, str]]) -> list[dict]:
    body = "\n\n".join(f"DRAFT {i + 1} ({name}):\n{text}" for i, (name, text) in enumerate(drafts))
    return [
        {"role": "system", "content": AGGREGATOR_SYSTEM},
        {"role": "user", "content": f"QUESTION:\n{question}\n\n{body}"},
    ]
