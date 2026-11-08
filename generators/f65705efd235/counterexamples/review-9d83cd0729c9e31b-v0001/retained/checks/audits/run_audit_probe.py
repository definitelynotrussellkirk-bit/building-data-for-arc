#!/usr/bin/env python3
"""Reproduce the two findings-only adversarial audit observations.

This script is intentionally read-only with respect to repository sources.  It
loads each assigned generator directly, compares deterministic override draws,
and extracts the canonical width-2 rectangle counterexample for f65705efd235.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))

ASSIGNED_HASHES = {
    "f65705efd235": "78f37b7191bd888d1a6038339a21142650a16732ab4ee142b9bb95496c3c275e",
    "ea61d17502dd": "0ef9e4dee146770a6458aef7bea5688d5ae573f2dc8d22fd9de3b42e3782b608",
}


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest_grid(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    actual = sha256_bytes(path.read_bytes())
    expected = ASSIGNED_HASHES[task_id]
    if actual != expected:
        raise RuntimeError(f"audit target hash changed for {task_id}: {actual} != {expected}")
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, actual


def canonical_task(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(task_id)


def normalized_rows(grid: list[str] | list[list[int]]) -> list[list[int]]:
    if grid and isinstance(grid[0], str):
        return [[int(cell) for cell in row] for row in grid]  # type: ignore[arg-type]
    return [list(row) for row in grid]  # type: ignore[arg-type]


def rectangle_bboxes(grid: list[str] | list[list[int]]) -> list[dict[str, Any]]:
    rows = normalized_rows(grid)
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value:
                positions[value].append((r, c))
    result = []
    for color, cells in sorted(positions.items()):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        result.append(
            {
                "color": color,
                "height": max(rs) - min(rs) + 1,
                "width": max(cs) - min(cs) + 1,
                "cells": [list(cell) for cell in cells],
            }
        )
    return result


def crossing_summary(grid: list[list[int]]) -> dict[str, int]:
    h = len(grid)
    w = len(grid[0])
    row_counts = [sum(value != 0 for value in row) for row in grid]
    col_counts = [sum(grid[r][c] != 0 for r in range(h)) for c in range(w)]
    row = max(range(h), key=row_counts.__getitem__)
    col = max(range(w), key=col_counts.__getitem__)
    return {"row": row, "col": col, "value": grid[row][col]}


def main() -> None:
    seed = 314159
    sample_index = 7
    difficulty = "medium"

    f657, f657_hash = load_generator("f65705efd235")
    f657_base = f657.generate(seed, sample_index, difficulty=difficulty)
    f657_variants = {
        "n_rects=1": f657.generate(seed, sample_index, difficulty=difficulty, n_rects=1),
        "n_rects=8": f657.generate(seed, sample_index, difficulty=difficulty, n_rects=8),
        "grid_h=5,grid_w=6": f657.generate(
            seed, sample_index, difficulty=difficulty, grid_h=5, grid_w=6
        ),
        "palette_kind=warm": f657.generate(
            seed, sample_index, difficulty=difficulty, palette_kind="warm"
        ),
        "unknown=123": f657.generate(seed, sample_index, difficulty=difficulty, unknown=123),
    }
    canonical = canonical_task("f65705efd235")
    canonical_train_3 = canonical["train"][3]
    bboxes = rectangle_bboxes(canonical_train_3["input"])
    width_two = [box for box in bboxes if box["width"] == 2]
    if not width_two:
        raise AssertionError("expected canonical width-2 rectangle counterexample")

    ea61, ea61_hash = load_generator("ea61d17502dd")
    ea61_base = ea61.generate(seed, sample_index, difficulty=difficulty)
    horizontal = ea61.generate(seed, sample_index, difficulty=difficulty, primary="horizontal")
    vertical = ea61.generate(seed, sample_index, difficulty=difficulty, primary="vertical")
    banana = ea61.generate(seed, sample_index, difficulty=difficulty, primary="banana")
    ea61_variants = {
        "anchor_corner=False": ea61.generate(
            seed, sample_index, difficulty=difficulty, anchor_corner=False
        ),
        "anchor_corner=True": ea61.generate(
            seed, sample_index, difficulty=difficulty, anchor_corner=True
        ),
        "asymmetry_force=False": ea61.generate(
            seed, sample_index, difficulty=difficulty, asymmetry_force=False
        ),
        "asymmetry_force=True": ea61.generate(
            seed, sample_index, difficulty=difficulty, asymmetry_force=True
        ),
        "palette_kind=warm": ea61.generate(
            seed, sample_index, difficulty=difficulty, palette_kind="warm"
        ),
        "palette_kind=cool": ea61.generate(
            seed, sample_index, difficulty=difficulty, palette_kind="cool"
        ),
        "unknown=123": ea61.generate(seed, sample_index, difficulty=difficulty, unknown=123),
    }

    result = {
        "schema": "arcpuzzles-adversarial-audit-probe-v1",
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "targets": {
            "f65705efd235": {
                "generator_sha256": f657_hash,
                "base_shape": [len(f657_base), len(f657_base[0])],
                "base_digest": digest_grid(f657_base),
                "override_observations": {
                    name: {
                        "same_as_base": grid == f657_base,
                        "shape": [len(grid), len(grid[0])],
                        "digest": digest_grid(grid),
                    }
                    for name, grid in f657_variants.items()
                },
                "canonical_train_3": {
                    "input": canonical_train_3["input"],
                    "output": canonical_train_3["output"],
                    "rectangle_bboxes": bboxes,
                    "width_two_counterexamples": width_two,
                },
            },
            "ea61d17502dd": {
                "generator_sha256": ea61_hash,
                "base_shape": [len(ea61_base), len(ea61_base[0])],
                "base_digest": digest_grid(ea61_base),
                "valid_primary_observations": {
                    "horizontal_digest": digest_grid(horizontal),
                    "horizontal_crossing": crossing_summary(horizontal),
                    "vertical_digest": digest_grid(vertical),
                    "vertical_crossing": crossing_summary(vertical),
                    "different": horizontal != vertical,
                },
                "invalid_primary_observation": {
                    "banana_digest": digest_grid(banana),
                    "banana_crossing": crossing_summary(banana),
                    "same_as_vertical": banana == vertical,
                    "self_check_errors": ea61.self_check(banana, difficulty=difficulty),
                },
                "ignored_or_unknown_override_observations": {
                    name: {
                        "same_as_base": grid == ea61_base,
                        "shape": [len(grid), len(grid[0])],
                        "digest": digest_grid(grid),
                        "self_check_errors": ea61.self_check(grid, difficulty=difficulty),
                    }
                    for name, grid in ea61_variants.items()
                },
            },
        },
    }

    # These assertions make the evidence command fail if the findings cease to reproduce.
    assert all(
        item["same_as_base"]
        for item in result["targets"]["f65705efd235"]["override_observations"].values()
    )
    assert result["targets"]["ea61d17502dd"]["valid_primary_observations"]["different"]
    assert result["targets"]["ea61d17502dd"]["invalid_primary_observation"]["same_as_vertical"]
    assert result["targets"]["ea61d17502dd"]["invalid_primary_observation"]["self_check_errors"] == []
    assert all(
        item["same_as_base"]
        for item in result["targets"]["ea61d17502dd"][
            "ignored_or_unknown_override_observations"
        ].values()
    )

    out = Path(__file__).with_name("audit_probe.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
