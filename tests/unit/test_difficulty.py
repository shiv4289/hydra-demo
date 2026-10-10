from hydra.difficulty import classify
from tests.conftest import EASY, HARD


def test_easy_prompt():
    d = classify(EASY)
    assert d.tier == "easy"


def test_hard_prompt_has_reasoning_signals():
    d = classify(HARD)
    assert d.tier == "hard"
    assert "design" in d.signals["keywords"]


def test_medium_prompt():
    assert classify("Explain how TCP slow start works and why it exists.").tier == "medium"


def test_code_bumps_difficulty():
    plain = classify("fix this")
    code = classify("fix this\n```python\ndef f(x): return x\n```")
    assert code.score > plain.score


def test_deterministic():
    assert classify(HARD) == classify(HARD)
