#!/usr/bin/env python3
"""Source-bound canonical-domain and teaching-gap probe for 9e11fddfa38a."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs, load_selected_generator  # noqa: E402

TASK_ID = "9e11fddfa38a"
DIFFICULTIES = ("easy", "medium", "hard")
SEEDS = range(100)


def grid_sha(grid: list[list[int]]) -> str:
    body = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(body).hexdigest()


def anti_reflect(n: int, r: int, c: int) -> tuple[int, int]:
    return n - 1 - c, n - 1 - r


def geometry(grid: list[list[int]]) -> dict[str, Any]:
    n = len(grid)
    axis = []
    collisions = []
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            mirror = anti_reflect(n, r, c)
            if mirror == (r, c):
                axis.append({"position": [r, c], "value": value})
            elif grid[mirror[0]][mirror[1]] != 0:
                pair = tuple(sorted(((r, c), mirror)))
                if pair not in seen:
                    seen.add(pair)
                    collisions.append(
                        {
                            "positions": [list(pair[0]), list(pair[1])],
                            "values": [grid[pair[0][0]][pair[0][1]], grid[pair[1][0]][pair[1][1]]],
                        }
                    )
    return {
        "axis_cells": axis,
        "axis_cell_count": len(axis),
        "occupied_reflection_pairs": collisions,
        "occupied_reflection_pair_count": len(collisions),
    }


def preserve_occupied_rival(grid: list[list[int]]) -> list[list[int]]:
    """Echo to empty reflected destinations but never replace an occupied original."""
    n = len(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            mr, mc = anti_reflect(n, r, c)
            if grid[mr][mc] == 0:
                out[mr][mc] = value
    return out


def differing_cells(a: list[list[int]], b: list[list[int]]) -> list[dict[str, Any]]:
    return [
        {"position": [r, c], "expected": a[r][c], "rival": b[r][c]}
        for r in range(len(a))
        for c in range(len(a[r]))
        if a[r][c] != b[r][c]
    ]


def main() -> None:
    module, source, source_sha = load_selected_generator(TASK_ID, root=REPO)
    pairs = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    variant0 = [row for row in pairs if row["variant"] == 0]
    train = [row for row in variant0 if row["split"] == "train"]
    tests = [row for row in variant0 if row["split"] == "test"]
    collision_tests = [row for row in tests if geometry(row["input"])["occupied_reflection_pair_count"]]
    if not collision_tests:
        raise RuntimeError("No canonical collision test found")
    witness = collision_tests[0]
    rival = preserve_occupied_rival(witness["input"])
    diff = differing_cells(witness["output"], rival)

    canonical_fit = []
    for pair in train:
        pred = preserve_occupied_rival(pair["input"])
        canonical_fit.append(
            {
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "fits": pred == pair["output"],
                "input_sha256": grid_sha(pair["input"]),
            }
        )

    population = []
    unique = set()
    axis_total = 0
    collision_total = 0
    validator_failures = 0
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            grid = module.generate(seed, 0, difficulty=difficulty)
            facts = geometry(grid)
            digest = grid_sha(grid)
            unique.add(digest)
            errors = module.self_check(grid, difficulty=difficulty)
            axis_total += int(facts["axis_cell_count"] > 0)
            collision_total += int(facts["occupied_reflection_pair_count"] > 0)
            validator_failures += int(bool(errors))
            population.append(
                {
                    "seed": seed,
                    "sample_index": 0,
                    "difficulty": difficulty,
                    "input_sha256": digest,
                    "axis_cell_count": facts["axis_cell_count"],
                    "occupied_reflection_pair_count": facts["occupied_reflection_pair_count"],
                    "validator_errors": errors,
                }
            )

    witness_geometry = geometry(witness["input"])
    validator_errors = module.self_check(witness["input"])
    report = {
        "schema": "arcpuzzles-local-audit-probe-v1",
        "task_id": TASK_ID,
        "finding_id": "A-9E-CANONICAL-COLLISION-GAP",
        "status": "reproduced_defect",
        "generator_path": str(source.relative_to(REPO)),
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": source_sha,
        "canonical_witness": {
            "variant": witness["variant"],
            "split": witness["split"],
            "pair_index": witness["pair_index"],
            "input_sha256": grid_sha(witness["input"]),
            "input": witness["input"],
            "canonical_output": witness["output"],
            "geometry": witness_geometry,
            "target_validator_errors": validator_errors,
            "passes_target_validator": not validator_errors,
            "belongs_to_canonical_task_domain": True,
        },
        "plausible_rival": {
            "name": "echo_only_into_empty_destinations_preserve_occupied",
            "description": (
                "Copy each nonzero cell to its anti-diagonal reflection only when the "
                "destination was empty; preserve all occupied originals."
            ),
            "canonical_training_fit": canonical_fit,
            "fits_all_variant0_training_pairs": all(row["fits"] for row in canonical_fit),
            "training_pairs_checked": len(canonical_fit),
            "witness_rival_output": rival,
            "witness_differing_cells": diff,
            "witness_difference_count": len(diff),
        },
        "population": {
            "seed_range": [0, 99],
            "sample_index": 0,
            "difficulties": list(DIFFICULTIES),
            "draws": len(population),
            "unique_inputs": len(unique),
            "inputs_with_axis_cells": axis_total,
            "inputs_with_occupied_reflection_pairs": collision_total,
            "validator_failures": validator_failures,
            "records": population,
        },
        "cause": (
            "generate() explicitly removes anti-diagonal fixed points and reserves both members "
            "of every reflection pair; self_check() rejects occupied reflection pairs, even though "
            "canonical overlay semantics define them."
        ),
        "target_modified": False,
        "command": {
            "cwd": "WORK/repo",
            "argv": ["python3", "../checks/audit/9e11fddfa38a/probe.py"],
        },
    }
    (HERE / "input.json").write_text(json.dumps(witness["input"], indent=2) + "\n", encoding="utf-8")
    (HERE / "counterexample.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": source_sha,
        "train_fit": report["plausible_rival"]["fits_all_variant0_training_pairs"],
        "difference_count": len(diff),
        "draws": len(population),
        "unique_inputs": len(unique),
        "axis_hits": axis_total,
        "collision_hits": collision_total,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
