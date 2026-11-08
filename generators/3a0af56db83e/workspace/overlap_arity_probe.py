#!/usr/bin/env python3
"""Audit overlap multiplicities and lesson rivals for task 3a0af56db83e.

This is a reviewer tool, not production code.  It intentionally reads canonical
answers, so never use it during a visible-only solve.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "3a0af56db83e"


def _bootstrap_reviewer_support() -> None:
    try:
        import reviewer_support  # noqa: F401
        return
    except ModuleNotFoundError as exc:
        if exc.name != "reviewer_support":
            raise
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            return
    raise ModuleNotFoundError("reviewer_support")


_bootstrap_reviewer_support()
from reviewer_support import canonical_pairs, find_root  # noqa: E402

ROOT = find_root(__file__)


def _load_generator():
    module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name not in {
            "puzzle_generators.per_puzzle",
            f"puzzle_generators.per_puzzle.{TASK_ID}",
            module_name,
        }:
            raise
    source = ROOT / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("overlap_arity_probe_generator", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def multiplicities(grid: list[list[int]]) -> dict[str, int]:
    counts = {str(arity): 0 for arity in range(5)}
    for row in range(3):
        for col in range(len(grid[0])):
            arity = sum(grid[band * 3 + row][col] != 0 for band in range(4))
            counts[str(arity)] += 1
    return counts


def canonical_shortcut_results() -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    return {
        name: {
            "fits": sum(shortcut(item["input"]) == item["output"] for item in pairs),
            "denominator": len(pairs),
        }
        for name, shortcut in gen.CANONICAL_SHORTCUTS.items()
    }


def lesson_results(starts: int) -> dict[str, Any]:
    rows = []
    ambiguous = []
    for difficulty_index, difficulty in enumerate(("easy", "medium", "hard")):
        for start in range(starts):
            lesson_seed = 700_000 + difficulty_index * 10_000 + start
            demos = [
                pair(
                    gen.generate(
                        lesson_seed,
                        start + offset,
                        difficulty=difficulty,
                    )
                )
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = pair(
                gen.generate(
                    lesson_seed,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=difficulty,
                )
            )
            survivors = []
            query_disagreements = []
            for name, rival in gen.LESSON_COMPETITORS.items():
                fits = all(rival(item["input"]) == item["output"] for item in demos)
                differs = rival(query["input"]) != query["output"]
                if fits:
                    survivors.append(name)
                if fits and differs:
                    query_disagreements.append(name)
            record = {
                "difficulty": difficulty,
                "start": start,
                "demo_profiles": [gen.schedule_profile(0, start + i, difficulty) for i in range(gen.EXAMPLES_NEEDED)],
                "query_profile": gen.schedule_profile(0, start + gen.EXAMPLES_NEEDED, difficulty),
                "surviving_declared_rivals": survivors,
                "surviving_rivals_that_change_query": query_disagreements,
            }
            rows.append(record)
            if query_disagreements:
                ambiguous.append(record)
    return {
        "assembly": f"{gen.EXAMPLES_NEEDED} consecutive demonstrations; next sample as query",
        "starts_per_difficulty": starts,
        "lessons": len(rows),
        "ambiguous_lessons": len(ambiguous),
        "ambiguous_records": ambiguous,
        "records": rows,
    }


def distribution_results(samples: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for profile_index, profile in enumerate(gen.MASK_PROFILES):
        profile_rows = []
        unique = set()
        for width in (4, 6, 12):
            for sample_index in range(samples):
                grid = gen.generate(
                    900_000 + profile_index * 100_000 + width * 1000 + sample_index,
                    sample_index,
                    difficulty="hard",
                    grid_w=width,
                    mask_profile=profile,
                    palette_mode="varied",
                )
                observed = gen.observe_overrides(grid)
                counts = multiplicities(grid)
                profile_rows.append(
                    {
                        "width": width,
                        "sample_index": sample_index,
                        "multiplicities": counts,
                        "observed_profile": observed["mask_profile"],
                    }
                )
                unique.add(freeze(grid))
        result[profile] = {
            "draws": len(profile_rows),
            "unique_inputs": len(unique),
            "all_cover_arities_0_to_4": all(
                all(row["multiplicities"][str(arity)] > 0 for arity in range(5))
                for row in profile_rows
            ),
            "all_observe_exact_profile": all(
                row["observed_profile"] == profile for row in profile_rows
            ),
            "rows": profile_rows,
        }
    return result


def shortcut_counterexample() -> dict[str, Any]:
    shortcut_name, shortcut = next(iter(gen.CANONICAL_SHORTCUTS.items()))
    for sample_index in range(64):
        grid = gen.generate(
            1_100_000 + sample_index,
            sample_index,
            difficulty="hard",
            palette_mode="varied",
        )
        intended = gen.rule_mirror(grid)
        rival = shortcut(grid)
        if rival != intended:
            return {
                "shortcut": shortcut_name,
                "seed": 1_100_000 + sample_index,
                "sample_index": sample_index,
                "difficulty": "hard",
                "overrides": {"palette_mode": "varied"},
                "observed_overrides": gen.observe_overrides(grid),
                "input": copy.deepcopy(grid),
                "python_rule_mirror_output": intended,
                "rival_output": rival,
                "differing_cells": [
                    [row, col, intended[row][col], rival[row][col]]
                    for row in range(len(intended))
                    for col in range(len(intended[0]))
                    if intended[row][col] != rival[row][col]
                ],
            }
    raise RuntimeError("no generated canonical-shortcut counterexample in 64 draws")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--counterexample-out", type=Path)
    args = parser.parse_args()

    report = {
        "schema": "3a0af56db83e-overlap-arity-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "canonical_shortcuts": canonical_shortcut_results(),
        "lessons": lesson_results(args.starts),
        "distribution": distribution_results(args.samples),
        "shortcut_counterexample": shortcut_counterexample(),
        "limits": (
            "Finite checks over declared rivals and sampled generated inputs do not prove "
            "unique induction against every possible rule."
        ),
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    if args.counterexample_out:
        args.counterexample_out.parent.mkdir(parents=True, exist_ok=True)
        args.counterexample_out.write_text(
            json.dumps(report["shortcut_counterexample"]["input"], indent=2) + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
