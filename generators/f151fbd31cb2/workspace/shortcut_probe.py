#!/usr/bin/env python3
"""Replay canonical-shortcut claims and emit one exact generated witness.

This is intentionally source-bound: it loads the selected generator path and
iterates the generator's own declarations rather than maintaining a second list
of claimed rivals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_probe import canonical_pairs, load_generator, observed, rule_output


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gen = load_generator(args.generator)
    pairs = canonical_pairs()
    canonical_fit = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        canonical_fit[name] = {
            "fits": all(rival(pair["input"]) == pair["output"] for pair in pairs),
            "pairs_checked": len(pairs),
        }

    seed, sample_index = 73, 1
    overrides = {"shape_key": 1, "color_key": 6}
    grid = gen.generate(seed, sample_index, **overrides)
    intended = rule_output(grid)
    rivals = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        for name, rival in getattr(gen, namespace).items():
            rivals[f"{namespace}:{name}"] = {
                "differs_from_intended": rival(grid) != intended,
                "output": rival(grid),
            }

    payload = {
        "schema": "f151fbd31cb2-shortcut-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_sha256": _sha256(args.generator),
        "canonical_fit": canonical_fit,
        "witness": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": None,
            "overrides": overrides,
            "observed_axes": observed(grid),
            "self_check": gen.self_check(grid),
            "semantic_witnesses": {
                name: predicate(grid) for name, predicate in gen.SEMANTIC_WITNESSES.items()
            },
            "input": grid,
            "independent_intended_output": intended,
            "declared_rivals": rivals,
        },
        "limits": (
            "Finite declared-rival replay. It proves these named rivals fit the four "
            "usable canonical pairs and are refuted by this witness; it does not prove "
            "universal identifiability against undeclared hypotheses."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": payload["generator_sha256"],
        "canonical_fit": canonical_fit,
        "observed_axes": payload["witness"]["observed_axes"],
        "rivals_refuted": [name for name, result in rivals.items() if result["differs_from_intended"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
