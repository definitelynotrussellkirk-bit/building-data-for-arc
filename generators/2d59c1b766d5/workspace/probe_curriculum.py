#!/usr/bin/env python3
"""Fast, source-bound curriculum probe for task 2d59c1b766d5.

This is intentionally independent of the generator's private analysis helpers.
It checks canonical labels, records which declared rivals fit every canonical
pair, and exhaustively tests every start residue and query rotation of the
period-three six-pair lesson.  Use ``--racket`` to add selected-rule execution
for the canonical pairs and retained semantic witnesses.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2d59c1b766d5"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "gate_frame_curriculum_probe_target", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def differing_cells(left, right):
    return [
        [row, col, left[row][col], right[row][col]]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def _witness_summary(gen, profile: str, sample_index: int, seed: int):
    grid = gen.generate(
        seed,
        sample_index,
        grid_h=15,
        grid_w=20,
        profile=profile,
    )
    intended = gen.rule_output(grid)
    refutes = []
    differences = {}
    for name, rival in sorted(gen.SEMANTIC_RIVALS.items()):
        prediction = rival(grid)
        diff = differing_cells(intended, prediction)
        if diff:
            refutes.append(name)
            differences[name] = {
                "count": len(diff),
                "first_cells": diff[:12],
            }
    return {
        "seed": seed,
        "sample_index": sample_index,
        "overrides": {"grid_h": 15, "grid_w": 20, "profile": profile},
        "refutes": refutes,
        "differences": differences,
    }, grid, intended


def build_report(*, include_racket: bool = False, seed: int = 2401) -> dict[str, Any]:
    gen = load_generator()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)

    canonical_mirror = all(gen.rule_output(pair["input"]) == pair["output"] for pair in pairs)
    fitting = [
        name
        for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items())
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    ]

    period = int(gen.LESSON_SCHEDULE_PERIOD)
    pair_count = int(gen.EXAMPLES_NEEDED) + 1
    starts = []
    all_rotations_refute = True
    for start in range(period):
        grids = [gen.generate(seed, start + offset) for offset in range(pair_count)]
        labels = [gen.schedule_profile(seed, start + offset) for offset in range(pair_count)]
        rotations = []
        for query_index in range(pair_count):
            demo_indices = [i for i in range(pair_count) if i != query_index]
            survivors = []
            for name, rival in sorted(gen.LESSON_COMPETITORS.items()):
                if all(
                    rival(grids[i]) == gen.rule_output(grids[i])
                    for i in demo_indices
                ):
                    survivors.append(name)
            if survivors:
                all_rotations_refute = False
            rotations.append(
                {
                    "query_index": query_index,
                    "demo_profiles": [labels[i] for i in demo_indices],
                    "surviving_rivals": survivors,
                }
            )
        starts.append({"start": start, "profiles": labels, "rotations": rotations})

    sealed, sealed_grid, sealed_output = _witness_summary(gen, "sealed", 1, seed)
    diagonal, diagonal_grid, diagonal_output = _witness_summary(gen, "diagonal", 2, seed)

    report: dict[str, Any] = {
        "schema": "2d59c1b766d5-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": file_sha256(GENERATOR_PATH),
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "canonical": {
            "pair_count": len(pairs),
            "python_mirror_matches_labels": canonical_mirror,
            "shortcuts_fitting_all_pairs": fitting,
        },
        "schedule": {
            "period": period,
            "pair_count": pair_count,
            "starts": starts,
            "all_query_rotations_refute_every_rival": all_rotations_refute,
        },
        "witnesses": {"sealed": sealed, "diagonal": diagonal},
        "limits": [
            "Finite checks cover only the declared rivals.",
            "Fixed-seed schedule enumeration proves this deterministic schedule, not all conceivable rules.",
            "Python mirror parity is not selected-rule authority unless --racket is used.",
        ],
    }

    if include_racket:
        from arcpuzzles import Catalog

        grids = [pair["input"] for pair in pairs] + [sealed_grid, diagonal_grid]
        intended = [pair["output"] for pair in pairs] + [sealed_output, diagonal_output]
        applied = Catalog().apply(TASK_ID, grids, timeout=120)
        outputs = [item["output"] for item in applied["results"]]
        report["racket"] = {
            "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
            "all_valid": all(
                item["valid_output"] and item["error"] is None
                for item in applied["results"]
            ),
            "matches_python_and_canonical_labels": outputs == intended,
            "cases": len(grids),
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--racket", action="store_true", help="execute the selected Racket rule")
    parser.add_argument("--seed", type=int, default=2401, help="fixed schedule/witness seed")
    parser.add_argument("--compact", action="store_true", help="emit one-line JSON")
    args = parser.parse_args()
    report = build_report(include_racket=args.racket, seed=args.seed)
    print(json.dumps(report, indent=None if args.compact else 2, sort_keys=True))
    ok = (
        report["canonical"]["python_mirror_matches_labels"]
        and report["schedule"]["all_query_rotations_refute_every_rival"]
    )
    if args.racket:
        ok = ok and all(
            report["racket"][key]
            for key in (
                "rule_hash_matches_catalog",
                "all_valid",
                "matches_python_and_canonical_labels",
            )
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
