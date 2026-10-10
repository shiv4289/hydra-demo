"""Demo CLI: fire prompts at strategies in-process (no server, no keys).

    python -m hydra.cli --all
    python -m hydra.cli -s hydra-cascade -p "Design a cache..." --trace
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .broker import Broker
from .samples import SAMPLES
from .strategies import StrategyError


def _short(s: str, n: int) -> str:
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def _print_trace(t) -> None:
    print(f"  strategy : {t.strategy} ({t.kind})")
    print(f"  decision : {t.reason}")
    for c in t.calls:
        extra = f" score={c.score:.2f}" if c.score is not None else ""
        status = "ok " if c.ok else "ERR"
        print(
            f"    {status} {c.role:<10} {c.backend:<8} {c.latency_ms:>7.1f} ms  "
            f"{c.prompt_tokens:>4}+{c.completion_tokens:<4} tok  ${c.cost_usd:.6f}{extra}"
            + (f"  {c.error}" if c.error else "")
        )
    print(
        f"  cost     : ${t.total_cost_usd:.6f} vs baseline ${t.baseline_cost_usd:.6f} "
        f"→ savings {t.savings_pct}%   wall {t.wall_ms:.0f} ms"
    )


async def _run(broker: Broker, strategies: list[str], prompts: list[str], trace: bool, as_json: bool) -> int:
    rows, out = [], []
    for s in strategies:
        for p in prompts:
            try:
                r = await broker.complete(s, [{"role": "user", "content": p}])
            except StrategyError as e:
                print(f"[{s}] ERROR: {e}", file=sys.stderr)
                continue
            t = r.trace
            rows.append((s, p, t))
            if as_json:
                out.append({"strategy": s, "prompt": p, "answer": r.completion.text, "hydra": t.model_dump()})
            elif trace:
                print(f"\n▶ [{s}] {_short(p, 90)}")
                print(f"  answer   : {_short(r.completion.text, 110)}")
                _print_trace(t)

    if as_json:
        print(json.dumps(out, indent=2))
        return 0

    print(f"\n{'strategy':<15} {'prompt':<42} {'selected':<8} {'calls':>5} {'cost $':>10} {'save %':>7}")
    print("-" * 92)
    for s, p, t in rows:
        print(f"{s:<15} {_short(p, 42):<42} {t.selected_backend:<8} {len(t.calls):>5} {t.total_cost_usd:>10.6f} {t.savings_pct:>7}")

    print(f"\n{'strategy':<15} {'total cost $':>13} {'baseline $':>12} {'savings %':>10} {'avg wall ms':>12}")
    print("-" * 66)
    for s in strategies:
        ts = [t for st, _, t in rows if st == s]
        if not ts:
            continue
        cost = sum(t.total_cost_usd for t in ts)
        base = sum(t.baseline_cost_usd for t in ts)
        save = (base - cost) / base * 100 if base else 0
        wall = sum(t.wall_ms for t in ts) / len(ts)
        print(f"{s:<15} {cost:>13.6f} {base:>12.6f} {save:>10.1f} {wall:>12.0f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hydra", description="Hydra broker demo CLI")
    ap.add_argument("-c", "--config", help="config path (default: $HYDRA_CONFIG or hydra.yaml)")
    ap.add_argument("-s", "--strategy", action="append", help="strategy or backend name (repeatable)")
    ap.add_argument("-p", "--prompt", action="append", help="custom prompt (repeatable); default: bundled samples")
    ap.add_argument("--all", action="store_true", help="run every configured strategy")
    ap.add_argument("--trace", action="store_true", help="print the full decision trace per request")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fast", action="store_true", help="10x faster mock latency")
    args = ap.parse_args(argv)

    broker = Broker.from_file(args.config)
    if args.fast:
        for b in broker.backends.values():
            if hasattr(b, "time_scale"):
                b.time_scale *= 0.1
    strategies = list(broker.strategies) if args.all or not args.strategy else args.strategy
    return asyncio.run(_run(broker, strategies, args.prompt or SAMPLES, args.trace, args.json))


if __name__ == "__main__":
    raise SystemExit(main())
