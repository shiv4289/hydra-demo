"""Bundled demo prompts: a realistic mix where most traffic is easy."""

SAMPLES: list[str] = [
    "hi! what's 2 + 2?",
    "What is the capital of Japan?",
    "Translate 'good morning' to Hindi.",
    "Give me a one-line definition of Kubernetes.",
    "Suggest a name for a golden retriever puppy.",
    "Summarize what a write-ahead log is in two sentences.",
    "Explain how TCP slow start works and why it exists.",
    (
        "Design a rate limiter for a multi-tenant inference API. Compare token bucket vs "
        "sliding window, analyze the trade-offs for bursty LLM traffic, and explain step by "
        "step how you would make it work across 3 gateway replicas without a single point of failure."
    ),
]
