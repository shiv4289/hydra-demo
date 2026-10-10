"""US5 + SC-001."""

import json

from hydra.cli import main


def test_cli_all_prints_summary(capsys):
    assert main(["-c", "hydra.yaml", "--all", "--fast"]) == 0
    out = capsys.readouterr().out
    for s in ("hydra-route", "hydra-cascade", "hydra-fusion"):
        assert s in out
    assert "savings %" in out


def test_sc001_cascade_saves_40pct_on_samples(capsys):
    main(["-c", "hydra.yaml", "-s", "hydra-cascade", "--json", "--fast"])
    rows = json.loads(capsys.readouterr().out)
    cost = sum(r["hydra"]["total_cost_usd"] for r in rows)
    base = sum(r["hydra"]["baseline_cost_usd"] for r in rows)
    assert (base - cost) / base >= 0.40


def test_cli_trace_mode(capsys):
    main(["-c", "hydra.yaml", "-s", "hydra-cascade", "-p", "hi", "--trace", "--fast"])
    out = capsys.readouterr().out
    assert "decision :" in out and "attempt" in out
