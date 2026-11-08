#!/usr/bin/env python3
"""Audit every cyclic lesson start against the generator's declared rivals.

This is a cheap Python-side complement to the source-bound lesson census.  It
uses ``rule_mirror`` rather than Racket, so it is suitable for rapid iteration,
not authority evidence.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys

TASK_ROOT = Path(__file__).resolve().parents[1]
for parent in TASK_ROOT.parents:
    if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent / "shared/runtime"))
        break
    if (parent / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent))
        break
else:  # pragma: no cover - packaging/runtime contract
    raise RuntimeError("No independent puzzle_generators runtime found")

spec = importlib.util.spec_from_file_location("probed_cf09cffb4663", TASK_ROOT / "generator.py")
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def _compact(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def audit(*, seed: int = 0, starts=range(6), bands=("easy", "medium", "hard")) -> dict:
    starts = tuple(int(value) for value in starts)
    bands = tuple(bands)
    failures: list[dict] = []
    refuted = Counter()
    profile_counts = Counter()
    unique_inputs = set()
    windows = 0

    for band in bands:
        for start in starts:
            windows += 1
            pairs = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(seed, sample_index, difficulty=band)
                unique_inputs.add(_compact(grid))
                profile_counts[gen.schedule_profile(seed, sample_index, band)] += 1
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            demos, query = pairs[:-1], pairs[-1]
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                failures.append({
                    "band": band,
                    "start": start,
                    "kind": "lesson_identifiable",
                    "reasons": reasons,
                })
            for name, rival in sorted(gen.LESSON_COMPETITORS.items()):
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    refuted[name] += 1
                else:
                    failures.append({
                        "band": band,
                        "start": start,
                        "kind": "surviving_competitor",
                        "competitor": name,
                    })

    return {
        "schema": "cf09cffb4663-cyclic-probe-v1",
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "seed": seed,
        "bands": list(bands),
        "starts": list(starts),
        "windows": windows,
        "competitors": sorted(gen.LESSON_COMPETITORS),
        "refuted_windows": dict(sorted(refuted.items())),
        "profiles": dict(sorted(profile_counts.items())),
        "unique_inputs": len(unique_inputs),
        "failures": failures,
        "limits": [
            "Python rule_mirror, not selected Racket authority.",
            "Finite declared rivals, not universal identifiability.",
            "Each start tests three demos plus the following query.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--starts", type=int, default=18,
                        help="number of consecutive starts beginning at zero")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(seed=args.seed, starts=range(args.starts))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
