#!/usr/bin/env python3
"""Fresh source-bound adversarial audit probe for 9e11fddfa38a."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "9e11fddfa38a"
DIFFICULTIES = ("easy", "medium", "hard")


def digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def reflect(n: int, r: int, c: int) -> tuple[int, int]:
    return n - 1 - c, n - 1 - r


def facts(grid: list[list[int]]) -> dict[str, Any]:
    n = len(grid)
    axis: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            mr, mc = reflect(n, r, c)
            if (mr, mc) == (r, c):
                axis.append({"position": [r, c], "value": value})
            elif grid[mr][mc] != 0:
                pair = tuple(sorted(((r, c), (mr, mc))))
                if pair not in seen:
                    seen.add(pair)
                    collisions.append({
                        "positions": [list(pair[0]), list(pair[1])],
                        "values": [grid[pair[0][0]][pair[0][1]], grid[pair[1][0]][pair[1][1]]],
                    })
    return {"axis_cells": axis, "occupied_reflection_pairs": collisions}


def preserve_occupied(grid: list[list[int]]) -> list[list[int]]:
    n = len(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            mr, mc = reflect(n, r, c)
            if grid[mr][mc] == 0:
                out[mr][mc] = value
    return out


def diffs(a: list[list[int]], b: list[list[int]]) -> list[dict[str, Any]]:
    return [
        {"position": [r, c], "authority": a[r][c], "rival": b[r][c]}
        for r in range(len(a)) for c in range(len(a[r])) if a[r][c] != b[r][c]
    ]


def main() -> None:
    repo = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK_ID, root=repo)
    pairs = [p for p in canonical_pairs(TASK_ID, root=repo, labeled_only=True) if p["variant"] == 0]
    train = [p for p in pairs if p["split"] == "train"]
    tests = [p for p in pairs if p["split"] == "test"]
    witness = next(p for p in tests if facts(p["input"])["occupied_reflection_pairs"])
    rival_output = preserve_occupied(witness["input"])
    train_fit = [
        {"pair_index": p["pair_index"], "fits": preserve_occupied(p["input"]) == p["output"],
         "input_sha256": digest(p["input"])}
        for p in train
    ]

    records: list[dict[str, Any]] = []
    unique: set[str] = set()
    axis_hits = collision_hits = validator_failures = 0
    for difficulty in DIFFICULTIES:
        for seed in range(100):
            grid = module.generate(seed, 0, difficulty=difficulty)
            geo = facts(grid)
            errors = module.self_check(grid, difficulty=difficulty)
            unique.add(digest(grid))
            axis_hits += bool(geo["axis_cells"])
            collision_hits += bool(geo["occupied_reflection_pairs"])
            validator_failures += bool(errors)
            records.append({
                "difficulty": difficulty, "seed": seed, "sample_index": 0,
                "input_sha256": digest(grid), "axis_cell_count": len(geo["axis_cells"]),
                "occupied_reflection_pair_count": len(geo["occupied_reflection_pairs"]),
                "validator_errors": errors,
            })

    report = {
        "schema": "arcpuzzles-local-audit-probe-v2",
        "task_id": TASK_ID,
        "finding_id": "A1-canonical-collision-teaching-gap",
        "status": "reproduced_defect",
        "prior_return_used_as_lead": "review-260b679b826b01a2:v0002",
        "generator_path": str(source.relative_to(repo)),
        "generator_sha256": source_sha,
        "generator_version": getattr(module, "VERSION", None),
        "canonical_witness": {
            "variant": witness["variant"], "split": witness["split"],
            "pair_index": witness["pair_index"], "input_sha256": digest(witness["input"]),
            "input": witness["input"], "canonical_output": witness["output"],
            "geometry": facts(witness["input"]),
            "validator_errors": module.self_check(witness["input"]),
            "belongs_to_canonical_domain": True,
        },
        "rival": {
            "name": "echo_only_into_empty_destinations_preserve_occupied",
            "training_fit": train_fit,
            "fits_all_training_pairs": all(x["fits"] for x in train_fit),
            "rival_output": rival_output,
            "differing_cells": diffs(witness["output"], rival_output),
        },
        "population": {
            "seed_range": [0, 99], "sample_index": 0,
            "difficulties": list(DIFFICULTIES), "draws": len(records),
            "unique_inputs": len(unique), "inputs_with_axis_cells": axis_hits,
            "inputs_with_occupied_reflection_pairs": collision_hits,
            "validator_failures": validator_failures, "records": records,
        },
        "target_modified": False,
        "command": {"cwd": "repo", "argv": ["python3", "../checks/audit/9e11fddfa38a/probe.py"]},
    }
    here = Path(__file__).resolve().parent
    (here / "input.json").write_text(json.dumps(witness["input"], indent=2) + "\n")
    (here / "counterexample.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "generator_sha256": source_sha,
        "train_fit": report["rival"]["fits_all_training_pairs"],
        "difference_count": len(report["rival"]["differing_cells"]),
        "draws": len(records), "unique_inputs": len(unique),
        "axis_hits": axis_hits, "collision_hits": collision_hits,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
