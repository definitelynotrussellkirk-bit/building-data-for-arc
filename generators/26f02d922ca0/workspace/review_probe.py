#!/usr/bin/env python3
"""Emit deterministic, machine-checkable shortcut counterexamples.

This is intentionally task-local.  It lets a future reviewer reproduce the
semantic evidence without learning the full battery command surface first:

    python3 generators/26f02d922ca0/workspace/review_probe.py \
        --seed 91 --difficulty hard

The JSON includes the generated grids, the Python authority output, every
finite rival's output, fired witness names, and whether each shortcut still
fits all real canonical pairs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO = HERE.parents[3]
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_generator():
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location(
        "generator_26f02d922ca0_review_probe", TASK_DIR / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not construct generator import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row(task_id: str) -> dict[str, Any]:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(f"canonical task {task_id!r} not found in {CANONICAL}")


def _canonical_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for split in ("train", "test"):
        value = row.get(split, [])
        if isinstance(value, list):
            pairs.extend(value)
        elif isinstance(value, dict):
            pairs.append(value)
    return pairs


def build_report(seed: int = 91, difficulty: str = "hard") -> dict[str, Any]:
    gen = _load_generator()
    row = _canonical_row(gen.TASK_ID)
    canonical_pairs = _canonical_pairs(row)
    normalized_rule = " ".join(row["program_solution"].split())
    actual_rule_hash = hashlib.sha256(normalized_rule.encode()).hexdigest()[:12]

    examples: list[dict[str, Any]] = []
    for sample_index in range(len(gen.SCHEDULE_PROFILES)):
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        oracle_output = gen.rule_mirror(grid)
        analysis = gen._analysis(grid)
        if analysis["errors"]:
            raise AssertionError(
                f"generated example {sample_index} is invalid: {analysis['errors']}"
            )
        rivals: dict[str, dict[str, Any]] = {}
        for name, rival in sorted(gen.SEMANTIC_RIVALS.items()):
            rival_output = rival(grid)
            rivals[name] = {
                "output": rival_output,
                "disagrees": rival_output != oracle_output,
            }
        examples.append(
            {
                "sample_index": sample_index,
                "profile": gen.schedule_profile(seed, sample_index, difficulty),
                "dimensions": [len(grid), len(grid[0])],
                "candidate_colours_in_reading_order": [
                    candidate["colour"] for candidate in analysis["candidates"]
                ],
                "witnesses": sorted(
                    name
                    for name, predicate in gen.SEMANTIC_WITNESSES.items()
                    if predicate(grid)
                ),
                "grid": grid,
                "oracle_output": oracle_output,
                "rivals": rivals,
            }
        )

    canonical_fits = {
        name: all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs)
        for name, shortcut in sorted(gen.CANONICAL_SHORTCUTS.items())
    }
    generator_bytes = (TASK_DIR / "generator.py").read_bytes()
    return {
        "schema_version": 1,
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "authority": {
            "rule_hash": actual_rule_hash,
            "declared_rule_hash": gen.RULE_HASH,
            "rule_hash_matches": actual_rule_hash == gen.RULE_HASH,
            "canonical_pair_count": len(canonical_pairs),
            "generator_sha256": hashlib.sha256(generator_bytes).hexdigest(),
        },
        "canonical_shortcuts_fit_all_pairs": canonical_fits,
        "examples": examples,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=91)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="hard"
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    payload = json.dumps(
        build_report(seed=args.seed, difficulty=args.difficulty),
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.out is None:
        sys.stdout.write(payload)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
