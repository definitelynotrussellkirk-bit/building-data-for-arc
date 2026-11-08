"""Finite demonstration-only rival audit for 6387de413b52."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_axis_role_audit_prototype", HERE / "prototype.py")
P = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(P)


def run_audit(*, seeds: Iterable[int] = (0, 17), demos_values: Iterable[int] = (2, 3, 6)) -> dict:
    harmful: list[dict] = []
    failures: list[dict] = []
    survivors: dict[str, int] = {}
    episodes = 0
    query_count = 0
    for seed in seeds:
        for demos in demos_values:
            for source in P.ROW_SOURCES:
                episodes += 1
                try:
                    episode = P.generate(seed, {"row_source": source}, demos, 4)
                except Exception as exc:
                    failures.append({"seed": seed, "demos": demos, "row_source": source,
                                     "error": f"{type(exc).__name__}: {exc}"})
                    continue
                query_count += len(episode["test"])
                names = sorted(P.rival_predictions(episode["train"][0]["input"], source))
                for name in names:
                    survives = all(P.rival_predictions(pair["input"], source)[name] == pair["output"]
                                   for pair in episode["train"])
                    if not survives:
                        continue
                    survivors[name] = survivors.get(name, 0) + 1
                    if any(P.rival_predictions(pair["input"], source)[name] != pair["output"]
                           for pair in episode["test"]):
                        harmful.append({"seed": seed, "demos": demos,
                                        "row_source": source, "rival": name})
    return {"schema": "6387de413b52-rival-audit-v1", "episodes": episodes,
            "queries": query_count, "survivor_counts": survivors,
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
