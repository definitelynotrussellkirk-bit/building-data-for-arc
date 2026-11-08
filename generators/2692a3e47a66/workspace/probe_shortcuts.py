#!/usr/bin/env python3
"""Replayable shortcut and lesson audit for generator 2692a3e47a66.

This tool deliberately uses the generator's own declared competitors and
witnesses.  It checks that every claimed canonical shortcut really fits every
public pair, materializes one generated disagreement for every witness, and
checks all cyclic starts of the four-example lesson schedule.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_ID = TASK_DIR.name
GENERATOR_PATH = TASK_DIR / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"shortcut_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs: list[dict[str, Any]] = []
            for split in ("train", "test"):
                value = row.get(split) or []
                if isinstance(value, dict):
                    value = [value]
                pairs.extend(
                    pair
                    for pair in value
                    if isinstance(pair, dict)
                    and isinstance(pair.get("input"), list)
                    and isinstance(pair.get("output"), list)
                )
            return pairs
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _same_grid(left, right) -> bool:
    return tuple(map(tuple, left)) == tuple(map(tuple, right))


def _diff_cells(left, right) -> int:
    return sum(
        a != b
        for left_row, right_row in zip(left, right)
        for a, b in zip(left_row, right_row)
    )


def _witness_grid(gen, witness, *, seed: int, start_index: int, difficulty: str):
    # Search the public profile grammar rather than keeping a duplicated
    # witness-to-profile lookup table in this tool.
    for offset, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(
            seed,
            start_index + offset,
            difficulty=difficulty,
            grid_h=17,
            grid_w=19,
            scene_profile=profile,
        )
        if witness(grid):
            return profile, start_index + offset, grid
    raise AssertionError("declared witness is not constructible by any public profile")


def build_report(
    *, seed: int = 71, start_index: int = 0, difficulty: str = "medium"
) -> dict[str, Any]:
    gen = _load_generator()
    pairs = _canonical_pairs()

    shortcuts: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = [
            _same_grid(rival(pair["input"]), pair["output"])
            for pair in pairs
        ]
        shortcuts[name] = {
            "canonical_matches": sum(matches),
            "canonical_pairs": len(matches),
            "fits_all_canonical_pairs": all(matches),
        }

    witnesses: dict[str, Any] = {}
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        profile, sample_index, grid = _witness_grid(
            gen,
            witness,
            seed=seed,
            start_index=start_index,
            difficulty=difficulty,
        )
        intended = gen.rule_mirror(grid)
        rivals = gen.WITNESS_RIVALS[witness_name]
        rival_outputs = {
            name: gen.SEMANTIC_RIVALS[name](grid)
            for name in rivals
        }
        witnesses[witness_name] = {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {
                "grid_h": 17,
                "grid_w": 19,
                "scene_profile": profile,
            },
            "observed_overrides": gen.observe_overrides(grid),
            "self_check": gen.self_check(grid),
            "input": grid,
            "intended_output": intended,
            "rivals": {
                name: {
                    "output": output,
                    "differing_cells": _diff_cells(intended, output),
                    "disagrees": not _same_grid(intended, output),
                }
                for name, output in rival_outputs.items()
            },
            "rival_disagrees": all(
                not _same_grid(intended, output)
                for output in rival_outputs.values()
            ),
        }

    surviving: dict[str, list[int]] = {}
    for cyclic_start in range(len(gen.SCENE_PROFILES)):
        demos = []
        for sample_index in range(
            cyclic_start, cyclic_start + gen.EXAMPLES_NEEDED
        ):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        for name, rival in gen.LESSON_COMPETITORS.items():
            if all(
                _same_grid(rival(pair["input"]), pair["output"])
                for pair in demos
            ):
                surviving.setdefault(name, []).append(cyclic_start)

    return {
        "schema": "arcpuzzles-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "seed": seed,
        "start_index": start_index,
        "difficulty": difficulty,
        "canonical_pairs": len(pairs),
        "canonical_shortcuts": shortcuts,
        "witnesses": witnesses,
        "cyclic_lesson_windows": {
            "checked": len(gen.SCENE_PROFILES),
            "surviving_competitors": surviving,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=71)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--difficulty", default="medium")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(
        seed=args.seed,
        start_index=args.start_index,
        difficulty=args.difficulty,
    )
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
