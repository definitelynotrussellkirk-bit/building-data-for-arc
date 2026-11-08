#!/usr/bin/env python3
"""Source-pinned finite shortcut probe for generator 5de3293e1bda.

The probe searches ordinary generated scenes for counterexamples to named wrong
rules.  It is supplementary evidence, not a universal identifiability proof or
an approval decision.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable, Iterable

TASK_ID = "5de3293e1bda"
EXPECTED_SOURCE_SHA256 = "4c5719dd689c89f380c366fdf707ccc5dffed604d5a426c137fc43d8512d4dc6"
def _find_repo_root() -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "generators/5de3293e1bda/generator.py").is_file():
            return candidate
    raise RuntimeError("run from the packet repo or set cwd to WORK/repo")


REPO_ROOT = _find_repo_root()
TASK_ROOT = REPO_ROOT / "generators/5de3293e1bda"
SOURCE_PATH = TASK_ROOT / "generator.py"
def _load_generator():
    spec = importlib.util.spec_from_file_location(f"shortcut_probe_generator_{TASK_ID}", SOURCE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load_generator()

Grid = list[list[int]]
Shape = frozenset[tuple[int, int]]


def _crop(cells: Shape) -> Grid:
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def _frame(cells: Shape, reference: Shape) -> Grid:
    if not reference:
        return [[0]]
    r1 = max(r for r, _ in reference)
    c1 = max(c for _, c in reference)
    return [[8 if (r, c) in cells else 0 for c in range(c1 + 1)] for r in range(r1 + 1)]


def _facts(grid: Grid) -> tuple[Shape, Shape, Shape, Shape, Shape]:
    info = MODULE._analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    blue = frozenset(info["blue_shape"])
    red = frozenset(info["red_shape"])
    inter = blue & red
    actual_blue = frozenset(info["blue_cells"])
    actual_red = frozenset(info["red_cells"])
    return blue, red, inter, actual_blue, actual_red


def _normalized_union(grid: Grid) -> Grid:
    blue, red, _inter, _actual_blue, _actual_red = _facts(grid)
    return _crop(blue | red)


def _normalized_xor(grid: Grid) -> Grid:
    blue, red, _inter, _actual_blue, _actual_red = _facts(grid)
    return _crop(blue ^ red)


def _blue_only(grid: Grid) -> Grid:
    blue, _red, _inter, _actual_blue, _actual_red = _facts(grid)
    return _crop(blue)


def _red_only(grid: Grid) -> Grid:
    _blue, red, _inter, _actual_blue, _actual_red = _facts(grid)
    return _crop(red)


def _absolute_intersection(grid: Grid) -> Grid:
    _blue, _red, _inter, actual_blue, actual_red = _facts(grid)
    cells = actual_blue & actual_red
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    normalized = frozenset((r - r0, c - c0) for r, c in cells)
    return _crop(normalized)


def _filled_overlap_bbox(grid: Grid) -> Grid:
    _blue, _red, inter, _actual_blue, _actual_red = _facts(grid)
    if not inter:
        return [[0]]
    rows = [r for r, _ in inter]
    cols = [c for _, c in inter]
    return [[8 for _ in range(max(cols) - min(cols) + 1)] for _ in range(max(rows) - min(rows) + 1)]


def _overlap_in_blue_frame(grid: Grid) -> Grid:
    blue, _red, inter, _actual_blue, _actual_red = _facts(grid)
    return _frame(inter, blue)


def _overlap_in_union_frame(grid: Grid) -> Grid:
    blue, red, inter, _actual_blue, _actual_red = _facts(grid)
    return _frame(inter, blue | red)


def _intersection_size_row(grid: Grid) -> Grid:
    _blue, _red, inter, _actual_blue, _actual_red = _facts(grid)
    return [[8] * len(inter)]


RIVALS: tuple[tuple[str, Callable[[Grid], Grid]], ...] = (
    ("normalized_union", _normalized_union),
    ("normalized_xor", _normalized_xor),
    ("blue_shape_only", _blue_only),
    ("red_shape_only", _red_only),
    ("absolute_spatial_intersection", _absolute_intersection),
    ("filled_overlap_bbox", _filled_overlap_bbox),
    ("overlap_in_blue_frame", _overlap_in_blue_frame),
    ("overlap_in_union_frame", _overlap_in_union_frame),
    ("intersection_size_row", _intersection_size_row),
)


def _grid_sha(grid: Grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _diff_cells(left: Grid, right: Grid) -> int:
    height = max(len(left), len(right))
    width = max(max(map(len, left), default=0), max(map(len, right), default=0))
    return sum(
        (left[r][c] if r < len(left) and c < len(left[r]) else None)
        != (right[r][c] if r < len(right) and c < len(right[r]) else None)
        for r in range(height)
        for c in range(width)
    )


def run_probe(*, seeds: Iterable[int] = range(12), difficulties: Iterable[str] = ("easy", "medium", "hard")) -> dict:
    source_sha = hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source hash mismatch: expected {EXPECTED_SOURCE_SHA256}, got {source_sha}")

    first: dict[str, dict | None] = {name: None for name, _ in RIVALS}
    cases = 0
    for difficulty in difficulties:
        for profile_index, profile in enumerate(MODULE.GENERAL_PROFILES):
            for seed in seeds:
                sample_index = 10_000 * profile_index + 101 * int(seed) + 13
                grid = MODULE.generate(int(seed), sample_index, difficulty=difficulty, scene_profile=profile)
                canonical = MODULE.rule_mirror(grid)
                cases += 1
                for name, rival in RIVALS:
                    if first[name] is not None:
                        continue
                    candidate = rival(grid)
                    changed = _diff_cells(canonical, candidate)
                    if changed:
                        first[name] = {
                            "difficulty": difficulty,
                            "profile": profile,
                            "seed": int(seed),
                            "sample_index": sample_index,
                            "input_shape": [len(grid), len(grid[0])],
                            "output_shape": [len(canonical), len(canonical[0])],
                            "differing_cells": changed,
                            "canonical_sha256": _grid_sha(canonical),
                            "rival_sha256": _grid_sha(candidate),
                        }

    unseparated = sorted(name for name, witness in first.items() if witness is None)
    rivals = [{"name": name, "first_counterexample": first[name]} for name, _ in RIVALS]
    counterexamples = [item for item in rivals if item["first_counterexample"] is not None]
    return {
        "schema": "arcpuzzles-bounded-shortcut-probe-v1",
        "task_id": TASK_ID,
        "source_path": f"generators/{TASK_ID}/generator.py",
        "source_sha256": source_sha,
        "status": "passed" if not unseparated else "finding",
        "scope": {
            "profiles": list(MODULE.GENERAL_PROFILES),
            "difficulties": list(difficulties),
            "seeds": [int(seed) for seed in seeds],
            "cases_examined": cases,
        },
        "rivals": rivals,
        "counterexamples": counterexamples,
        "unseparated_rivals": unseparated,
        "limitations": "Finite ordinary-generation probe only; it is not a uniqueness proof or acceptance decision.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seeds", type=int, nargs="*", default=list(range(12)))
    args = parser.parse_args()
    report = run_probe(seeds=args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
