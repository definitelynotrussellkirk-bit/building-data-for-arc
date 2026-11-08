#!/usr/bin/env python3
"""Inspect 81fdfd815936 samples, candidates, schedule roles, and rival answers.

Examples (from a staged repo runtime):
  python generators/81fdfd815936/workspace/review_probe.py --seed 7 --sample-index 0
  python generators/81fdfd815936/workspace/review_probe.py --sweep 100 --difficulty hard
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "81fdfd815936"
TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return [min(rows), min(cols), max(rows), max(cols)]


def _component_rows(module, grid):
    rows = []
    for index, (color, cells) in enumerate(module._components4(grid)):
        rows.append(
            {
                "index": index,
                "color": color,
                "bbox": _bbox(cells),
                "cells": len(cells),
                "lr_symmetric": module._is_lr_symmetric(cells),
                "crop": module._crop_component(grid, (color, cells)),
            }
        )
    return rows


def inspect(module, grid, *, seed=None, sample_index=None, difficulty=None):
    components = _component_rows(module, grid)
    candidates = [row for row in components if row["lr_symmetric"]]
    answer = module.rule_mirror(grid)
    rivals = {
        name: {
            "agrees": solver(grid) == answer,
            "output": solver(grid),
        }
        for name, solver in module.SEMANTIC_RIVALS.items()
    }
    return {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "schedule_profile": (
            module.schedule_profile(seed, sample_index, difficulty)
            if seed is not None and sample_index is not None
            else None
        ),
        "dimensions": [len(grid), len(grid[0])],
        "self_check": module.self_check(grid),
        "components": components,
        "candidate_indices": [row["index"] for row in candidates],
        "selected_index": candidates[0]["index"] if candidates else None,
        "answer": answer,
        "witnesses": {
            name: bool(predicate(grid))
            for name, predicate in module.SEMANTIC_WITNESSES.items()
        },
        "rivals": rivals,
        "grid": grid,
    }


def sweep(module, count: int, difficulty: str | None, seed: int):
    profile_counts: dict[str, int] = {}
    candidate_counts: dict[str, int] = {}
    rival_disagreements = {name: 0 for name in module.SEMANTIC_RIVALS}
    witness_counts = {name: 0 for name in module.SEMANTIC_WITNESSES}
    validation_errors: list[dict[str, Any]] = []
    outputs = set()
    for sample_index in range(count):
        grid = module.generate(seed, sample_index, difficulty=difficulty)
        errors = module.self_check(grid)
        if errors:
            validation_errors.append({"sample_index": sample_index, "errors": errors})
        profile = str(module.schedule_profile(seed, sample_index, difficulty))
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
        candidates = module._symmetric_candidates(grid)
        key = str(len(candidates))
        candidate_counts[key] = candidate_counts.get(key, 0) + 1
        answer = module.rule_mirror(grid)
        outputs.add(tuple(tuple(row) for row in answer))
        for name, rival in module.SEMANTIC_RIVALS.items():
            rival_disagreements[name] += int(rival(grid) != answer)
        for name, witness in module.SEMANTIC_WITNESSES.items():
            witness_counts[name] += int(bool(witness(grid)))
    return {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "seed": seed,
        "difficulty": difficulty,
        "samples": count,
        "profile_counts": profile_counts,
        "symmetric_candidate_counts": candidate_counts,
        "unique_outputs": len(outputs),
        "rival_disagreements": rival_disagreements,
        "witness_counts": witness_counts,
        "validation_errors": validation_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--grid-h", type=int)
    parser.add_argument("--grid-w", type=int)
    parser.add_argument("--sweep", type=int, metavar="N")
    args = parser.parse_args()

    module = _load_generator()
    difficulty = args.difficulty
    if args.sweep is not None:
        if args.sweep <= 0:
            parser.error("--sweep must be positive")
        payload = sweep(module, args.sweep, difficulty, args.seed)
    else:
        overrides = {
            key: value
            for key, value in {"grid_h": args.grid_h, "grid_w": args.grid_w}.items()
            if value is not None
        }
        grid = module.generate(
            args.seed,
            args.sample_index,
            difficulty=difficulty,
            **overrides,
        )
        payload = inspect(
            module,
            grid,
            seed=args.seed,
            sample_index=args.sample_index,
            difficulty=difficulty,
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
