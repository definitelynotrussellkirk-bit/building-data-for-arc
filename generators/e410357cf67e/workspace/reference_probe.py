#!/usr/bin/env python3
"""Small reviewer CLI for sampling e410357cf67e and checking declared rivals.

This deliberately uses only the public generator module plus its task-domain
analysis hooks.  It is useful when changing schedules or investigating a saved
seed because it prints exact axes, beam facts, and which rivals disagree.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("probe_e410357cf67e", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _digest(value: Any) -> str:
    data = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()


def inspect(seed: int, sample_index: int, difficulty: str | None) -> dict[str, Any]:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    truth = GEN.rule_mirror(grid)
    facts = GEN._analysis(grid)
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "axes": GEN.observe_overrides(grid),
        "self_check": GEN.self_check(grid),
        "analysis": {
            "source": facts["source"],
            "corner_source": facts["corner_source"],
            "hit_mirrors": facts["hit_mirrors"],
            "termination": facts["termination"],
            "active_wall": facts["active_wall"],
            "painted_cells": len(facts["path"]),
        },
        "input_sha256": _digest(grid),
        "output_sha256": _digest(truth),
        "rivals_refuted": [
            name for name, rival in GEN.SEMANTIC_RIVALS.items() if rival(grid) != truth
        ],
        "witnesses": [
            name for name, witness in GEN.SEMANTIC_WITNESSES.items() if witness(grid)
        ],
        "input": grid,
        "output": truth,
    }


def lesson(seed: int, start: int, difficulty: str | None) -> dict[str, Any]:
    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, start + offset, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    rotations = []
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        rotations.append(
            {
                "query_index": query_index,
                "reasons": GEN.lesson_identifiable(demos, query),
                "surviving_rivals": [
                    name
                    for name, rival in GEN.LESSON_COMPETITORS.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                ],
            }
        )
    return {
        "seed": seed,
        "start": start,
        "difficulty": difficulty,
        "profiles": [GEN.observe_overrides(pair["input"])["profile"] for pair in pairs],
        "rotations": rotations,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--lesson", action="store_true", help="also check all five query rotations")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    report = {
        "task_id": GEN.TASK_ID,
        "version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "samples": [
            inspect(args.seed, args.start + offset, args.difficulty)
            for offset in range(args.count)
        ],
    }
    if args.lesson:
        report["lesson"] = lesson(args.seed, args.start, args.difficulty)
    print(json.dumps(report, indent=None if args.compact else 2, sort_keys=True))


if __name__ == "__main__":
    main()
