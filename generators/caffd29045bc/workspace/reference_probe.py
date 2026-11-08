#!/usr/bin/env python3
"""Source-local semantic probe for caffd29045bc.

It is intentionally independent of the lesson-census wrapper: future reviewers
can replay canonical shortcut fit, generated counterexamples, and every holdout
of several four-profile windows with one command.  The canonical Racket remains
the label authority in the retained battery/census evidence; this probe uses the
source-local Python mirror only as a fast regression oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "caffd29045bc"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", GENERATOR_PATH)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _different_cells(left: list[list[int]], right: list[list[int]]) -> list[dict[str, int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("probe only compares same-shape outputs")
    return [
        {"row": row, "col": col, "intended": a, "rival": b}
        for row, (left_row, right_row) in enumerate(zip(left, right))
        for col, (a, b) in enumerate(zip(left_row, right_row))
        if a != b
    ]


def _label(gen, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def build_report(*, seed: int = 5_000, windows: int = 8) -> dict[str, Any]:
    gen = _load_generator()
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }

    counterexamples: dict[str, Any] = {}
    for sample_index in range(gen.LESSON_SCHEDULE_PERIOD):
        grid = gen.generate(seed, sample_index, difficulty="medium")
        intended = gen.rule_mirror(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            if name in counterexamples:
                continue
            rival_output = rival(grid)
            changes = _different_cells(intended, rival_output)
            if not changes:
                continue
            counterexamples[name] = {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": "medium",
                "profile": gen.schedule_profile(seed, sample_index, "medium"),
                "observed": gen.observe_overrides(grid),
                "witnesses": [
                    witness
                    for witness, predicate in gen.SEMANTIC_WITNESSES.items()
                    if predicate(grid)
                ],
                "different_cells": len(changes),
                "differences": changes,
                "input": grid,
                "intended_output": intended,
                "rival_output": rival_output,
            }

    rotation_failures: list[dict[str, Any]] = []
    rotations_checked = 0
    for start in range(windows):
        grids = [
            gen.generate(seed + start, start + offset, difficulty="medium")
            for offset in range(gen.EXAMPLES_NEEDED + 1)
        ]
        for held_out in range(len(grids)):
            rotations_checked += 1
            demos = [_label(gen, grid) for index, grid in enumerate(grids) if index != held_out]
            query = _label(gen, grids[held_out])
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                rotation_failures.append(
                    {"start": start, "held_out": held_out, "reasons": reasons}
                )

    source_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    return {
        "schema": "caffd29045bc-reference-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "canonical": {
            "pairs": len(canonical),
            "shortcut_fit": canonical_fit,
            "all_shortcuts_fit": bool(canonical_fit) and all(canonical_fit.values()),
        },
        "schedule": {
            "period": gen.LESSON_SCHEDULE_PERIOD,
            "profiles": list(gen.SCHEDULE_PROFILES),
            "windows": windows,
            "rotations_checked": rotations_checked,
            "rotation_failures": rotation_failures,
            "all_rotations_identifiable": not rotation_failures,
        },
        "counterexamples": counterexamples,
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=5_000)
    parser.add_argument("--windows", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report(seed=args.seed, windows=args.windows)
    write_report(args.out, report)
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "canonical_shortcuts_fit": report["canonical"]["all_shortcuts_fit"],
                "counterexamples": {
                    name: row["different_cells"]
                    for name, row in report["counterexamples"].items()
                },
                "rotations_checked": report["schedule"]["rotations_checked"],
                "rotation_failures": len(report["schedule"]["rotation_failures"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if (
        report["canonical"]["all_shortcuts_fit"]
        and len(report["counterexamples"]) == 4
        and report["schedule"]["all_rotations_identifiable"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
