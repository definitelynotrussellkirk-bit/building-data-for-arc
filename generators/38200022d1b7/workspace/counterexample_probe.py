#!/usr/bin/env python3
"""Emit an exact generated counterexample to the geometric-center shortcut.

The canonical demonstrations all place color 5 at the geometric grid center, so
"rotate around the grid center" fits them.  This probe materializes a lawful
off-center lesson input, computes both predictions with the generator's pure
helpers, and records the exact disagreeing outputs as JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"
_SPEC = importlib.util.spec_from_file_location("generator_38200022d1b7_probe", GENERATOR_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _pivot(grid: list[list[int]]) -> list[int]:
    pivots = [
        [r, c]
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected one color-5 pivot, found {len(pivots)}")
    return pivots[0]


def build_report(
    *,
    seed: int = 38200022,
    sample_index: int = 1,
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Build one source-bound, executable shortcut disagreement record."""
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    intended = GEN.rule_mirror(grid)
    shortcut = GEN.CANONICAL_SHORTCUTS["grid_center"](grid)
    pivot = _pivot(grid)
    center = [len(grid) // 2, len(grid[0]) // 2]
    self_check = GEN.self_check(grid)
    verified = not self_check and pivot != center and intended != shortcut
    return {
        "schema": "arc-shortcut-counterexample-v1",
        "task_id": GEN.TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": GEN.RULE_HASH,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "shortcut": "grid_center",
        "shortcut_claim": "Reflect every source around the geometric grid center.",
        "intended_claim": "Reflect every source around the unique color-5 pivot.",
        "pivot": pivot,
        "grid_center": center,
        "observed_axes": GEN.observe_overrides(grid),
        "self_check": self_check,
        "input": grid,
        "intended_output": intended,
        "shortcut_output": shortcut,
        "verified_disagreement": verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=38200022)
    parser.add_argument("--sample-index", type=int, default=1)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = build_report(
        seed=args.seed,
        sample_index=args.sample_index,
        difficulty=args.difficulty,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["verified_disagreement"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
