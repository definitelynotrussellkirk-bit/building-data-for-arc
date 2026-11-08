"""Finite demonstration-only rival audit for e68b376152cd."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_e68_audit_prototype", HERE / "prototype.py")
P = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(P)


def run_audit(*, seeds: Iterable[int] = (0, 17), demos_values: Iterable[int] = (2, 3, 6)) -> dict:
    harmful: list[dict] = []
    failures: list[dict] = []
    survivor_counts: dict[str, int] = {}
    episodes = 0
    query_count = 0
    for seed in seeds:
        for demos in demos_values:
            for policy in P.POLICIES:
                episodes += 1
                try:
                    episode = P.generate(seed, {"order_policy": policy}, demos, 4)
                except Exception as exc:  # retained as an audit failure, never rival elimination
                    failures.append({"seed": seed, "demos": demos, "policy": policy,
                                     "error": f"{type(exc).__name__}: {exc}"})
                    continue
                query_count += len(episode["test"])
                names = sorted(P.rival_predictions(episode["train"][0]["input"], policy))
                for name in names:
                    survives = all(P.rival_predictions(pair["input"], policy)[name] == pair["output"]
                                   for pair in episode["train"])
                    if not survives:
                        continue
                    survivor_counts[name] = survivor_counts.get(name, 0) + 1
                    disagrees = any(P.rival_predictions(pair["input"], policy)[name] != pair["output"]
                                    for pair in episode["test"])
                    if disagrees:
                        harmful.append({"seed": seed, "demos": demos, "policy": policy,
                                        "rival": name})
    return {"schema": "e68b376152cd-rival-audit-v1", "episodes": episodes,
            "queries": query_count, "survivor_counts": survivor_counts,
            "harmful_survivors": harmful, "input_failures": failures,
            "scope": "Finite Python mirror audit; protected Racket qualification is separate."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_audit()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
