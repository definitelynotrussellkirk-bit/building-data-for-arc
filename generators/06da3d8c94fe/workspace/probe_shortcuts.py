#!/usr/bin/env python3
"""Reproduce the strongest five-panel shortcut and audit lesson windows.

The main rival is ``never_union``: infer intersection/xor normally, but map a
union demonstration to xor.  It fits the two public training demonstrations
because neither demonstrates union, yet disagrees on the public query and on
scheduled generated union cases.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path

from reference_probe import (
    canonical_pairs,
    independent_rule,
    infer_kind,
    load_generator,
    never_union,
)

HERE = Path(__file__).resolve().parent
GENERATOR_DIR = HERE.parent


def _sha(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def counterexample_record(generator, *, seed: int, sample_index: int, difficulty: str | None):
    grid = generator.generate(seed, sample_index, difficulty=difficulty, kind="union")
    intended = independent_rule(grid)
    shortcut = never_union(grid)
    differing = [
        [row, column]
        for row in range(len(intended))
        for column in range(len(intended[0]))
        if intended[row][column] != shortcut[row][column]
    ]
    if not differing:
        raise AssertionError("selected draw did not refute never_union")
    return {
        "schema": "arcpuzzles-generator-counterexample-v1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "shortcut": "never_union",
        "shortcut_definition": (
            "Infer the demonstrated operation except replace union with xor; "
            "equivalently assume the two canonical training operations exhaust the task."
        ),
        "generation": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {"kind": "union"},
        },
        "input": grid,
        "intended_output": intended,
        "shortcut_output": shortcut,
        "differing_cells": differing,
        "input_sha256": _sha(grid),
        "intended_output_sha256": _sha(intended),
        "shortcut_output_sha256": _sha(shortcut),
        "checks": {
            "self_check": generator.self_check(grid),
            "inferred_kind": infer_kind(grid),
            "production_rival_matches_independent": (
                generator.SEMANTIC_RIVALS["never_union"](grid) == shortcut
            ),
            "intended_mirror_matches_independent": generator.rule_mirror(grid) == intended,
        },
    }


def lesson_window_report(generator, *, seed: int, start: int, difficulty: str | None):
    grids = [
        generator.generate(seed, start + offset, difficulty=difficulty)
        for offset in range(6)
    ]
    pairs = [{"input": grid, "output": independent_rule(grid)} for grid in grids]
    rotations = []
    for query_index in range(6):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        survivors = []
        for name, rival in generator.LESSON_COMPETITORS.items():
            if (
                rival(query["input"]) != query["output"]
                and all(rival(pair["input"]) == pair["output"] for pair in demos)
            ):
                survivors.append(name)
        rotations.append({
            "query_index": query_index,
            "query_kind": infer_kind(query["input"]),
            "surviving_query_changing_rivals": survivors,
        })
    return {
        "seed": seed,
        "start": start,
        "difficulty": difficulty,
        "kind_counts": dict(Counter(infer_kind(grid) for grid in grids)),
        "rotations": rotations,
    }


def build_report(generator, *, seed: int = 13000, sample_index: int = 0):
    canonical = canonical_pairs()
    canonical_fit = [never_union(pair["input"]) == pair["output"] for pair in canonical]
    return {
        "schema": "arcpuzzles-shortcut-probe-v1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "canonical": {
            "kinds": [infer_kind(pair["input"]) for pair in canonical],
            "never_union_matches": canonical_fit,
            "training_demonstrations_fit": all(canonical_fit[:2]),
            "query_disagrees": not canonical_fit[2],
        },
        "generated_counterexample": counterexample_record(
            generator,
            seed=seed,
            sample_index=sample_index,
            difficulty="easy",
        ),
        "lesson_windows": [
            lesson_window_report(generator, seed=seed + index, start=index, difficulty=band)
            for index, band in enumerate(("easy", "medium", "hard"))
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=os.environ.get("GENERATOR_UNDER_TEST"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--counterexample-out", type=Path)
    parser.add_argument("--seed", type=int, default=13000)
    parser.add_argument("--sample-index", type=int, default=0)
    args = parser.parse_args()
    generator = load_generator(args.generator)
    report = build_report(generator, seed=args.seed, sample_index=args.sample_index)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.counterexample_out:
        args.counterexample_out.parent.mkdir(parents=True, exist_ok=True)
        args.counterexample_out.write_text(
            json.dumps(report["generated_counterexample"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    bad_rotations = [
        rotation
        for lesson in report["lesson_windows"]
        for rotation in lesson["rotations"]
        if rotation["surviving_query_changing_rivals"]
    ]
    checks = report["generated_counterexample"]["checks"]
    return 0 if (
        report["canonical"]["training_demonstrations_fit"]
        and report["canonical"]["query_disagrees"]
        and not bad_rotations
        and checks["self_check"] == []
        and checks["production_rival_matches_independent"]
        and checks["intended_mirror_matches_independent"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
