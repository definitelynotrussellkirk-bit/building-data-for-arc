#!/usr/bin/env python3
"""Finite curriculum audit for the dominant-gap translation family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_audit_ac4b61e7b230_prototype", HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(HERE / "prototype.py")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = PROTOTYPE
_SPEC.loader.exec_module(PROTOTYPE)


def _translation(strategy: str, dr: int, dc: int) -> tuple[int, int]:
    if strategy == "all_axes":
        return dr, dc
    if strategy == "dominant_row_tie":
        return (dr, 0) if abs(dr) >= abs(dc) else (0, dc)
    if strategy == "row_only":
        return dr, 0
    if strategy == "column_only":
        return 0, dc
    if strategy == "smaller_gap_axis":
        if dr == 0:
            return 0, dc
        if dc == 0:
            return dr, 0
        return (dr, 0) if abs(dr) < abs(dc) else (0, dc)
    if strategy == "dominant_column_tie":
        return (dr, 0) if abs(dr) > abs(dc) else (0, dc)
    raise ValueError(strategy)


def _render(grid, strategy: str):
    analysis = PROTOTYPE.generator()._analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    dr, dc = _translation(strategy, *analysis["translation"])
    height, width = len(grid), len(grid[0])
    shifted = {(row + dr, col + dc) for row, col in analysis["red"]}
    if any(not 0 <= row < height or not 0 <= col < width for row, col in shifted):
        return None
    if shifted & analysis["cyan"]:
        return None
    output = [[0] * width for _ in range(height)]
    for row, col in analysis["cyan"]:
        output[row][col] = 8
    for row, col in shifted:
        output[row][col] = 2
    return output


def _input_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def audit(*, seed_start: int = 0, seed_count: int = 16) -> dict:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative literal integer")
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be a literal integer in 1..4096")

    failures = []
    episodes = 0
    exact_30x30_pairs = 0
    harmful_rival_survivors = 0
    setting_dependent_query_pairs = 0
    public_prefix_checks = 0
    mode_strategy = {
        "all_separated_axes": "all_axes",
        "dominant_gap_axis": "dominant_row_tie",
    }
    rival_strategies = (
        "row_only",
        "column_only",
        "smaller_gap_axis",
        "dominant_column_tie",
    )

    for seed in range(seed_start, seed_start + seed_count):
        pool = PROTOTYPE.sample_inputs(seed, demo_count=6, query_count=4)
        demonstrations = pool["demonstrations"]
        queries = pool["queries"]
        all_inputs = demonstrations + queries
        if len({_input_key(grid) for grid in all_inputs}) != 10:
            failures.append({"seed": seed, "finding": "duplicate_input"})
        stress = queries[-1]
        if len(stress) != 30 or len(stress[0]) != 30:
            failures.append({"seed": seed, "finding": "missing_exact_30x30_query"})
        if sum(cell != 0 for row in stress for cell in row) <= 100:
            failures.append({"seed": seed, "finding": "sparse_30x30_query"})
        if not (any(stress[0]) and any(stress[-1])
                and any(row[0] for row in stress) and any(row[-1] for row in stress)):
            failures.append({"seed": seed, "finding": "30x30_missing_boundary_contact"})

        matrices = {
            mode: [_render(grid, strategy) for grid in all_inputs]
            for mode, strategy in mode_strategy.items()
        }
        for query_index in range(6, 10):
            if len({PROTOTYPE.object_sha256(outputs[query_index]) for outputs in matrices.values()}) > 1:
                setting_dependent_query_pairs += 1

        for parameters in PROTOTYPE.ALL_PARAMETERS:
            truth = matrices[parameters.translation_mode]
            rivals = {
                name: [_render(grid, name) for grid in all_inputs]
                for name in rival_strategies
            }
            for demo_count in range(2, 7):
                episodes += 1
                exact_30x30_pairs += 1
                survivors = [
                    mode for mode, outputs in matrices.items()
                    if outputs[:demo_count] == truth[:demo_count]
                ]
                if survivors != [parameters.translation_mode]:
                    failures.append({
                        "seed": seed,
                        "setting": parameters.as_dict(),
                        "demo_count": demo_count,
                        "finding": "finite_setting_ambiguity",
                        "survivors": survivors,
                    })
                for name, outputs in rivals.items():
                    fits = outputs[:demo_count] == truth[:demo_count]
                    changes_query = any(
                        actual != expected
                        for actual, expected in zip(outputs[6:], truth[6:])
                    )
                    if fits and changes_query:
                        harmful_rival_survivors += 1
                        failures.append({
                            "seed": seed,
                            "setting": parameters.as_dict(),
                            "demo_count": demo_count,
                            "finding": "harmful_structural_rival",
                            "rival": name,
                        })

                episode = {
                    "train": [
                        {"input": deepcopy(grid), "output": deepcopy(output)}
                        for grid, output in zip(demonstrations[:demo_count], truth[:demo_count])
                    ],
                    "test": [
                        {"input": deepcopy(grid), "output": deepcopy(output)}
                        for grid, output in zip(queries, truth[6:])
                    ],
                    "program_solution": PROTOTYPE.materialize_rule(parameters),
                }
                first = PROTOTYPE.public_challenge(episode, revealed_queries=1)
                full = PROTOTYPE.public_challenge(episode, revealed_queries=4)
                public_prefix_checks += 1
                if first["train"] != full["train"] or first["test"] != full["test"][:1]:
                    failures.append({
                        "seed": seed,
                        "setting": parameters.as_dict(),
                        "demo_count": demo_count,
                        "finding": "public_prefix_instability",
                    })

    summary = {
        "seeds": seed_count,
        "settings": len(PROTOTYPE.ALL_PARAMETERS),
        "demo_counts": [2, 3, 4, 5, 6],
        "episodes": episodes,
        "exact_30x30_pairs": exact_30x30_pairs,
        "setting_dependent_query_pairs": setting_dependent_query_pairs,
        "public_prefix_checks": public_prefix_checks,
        "harmful_rival_survivors": harmful_rival_survivors,
        "failures": len(failures),
    }
    return {
        "schema": "arc-parametric-lesson-audit-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "status": "pass" if not failures else "fail",
        "summary": summary,
        "declared_structural_rivals": list(rival_strategies),
        "limitations": (
            "Finite audit over the declared settings, rivals, and requested seeds; "
            "not a proof of universal lesson uniqueness."
        ),
        "failures": failures,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit(seed_start=args.seed_start, seed_count=args.seeds)
    payload = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
