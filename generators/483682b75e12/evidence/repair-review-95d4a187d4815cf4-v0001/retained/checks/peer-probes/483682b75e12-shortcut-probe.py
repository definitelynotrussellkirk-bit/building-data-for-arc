#!/usr/bin/env python3
"""Source-pinned finite shortcut probe for generator 483682b75e12.

This is supplementary evidence only.  It checks that ordinary generated scenes
contain a concrete counterexample to each named, plausible wrong rule; it does
not approve the generator or prove universal uniqueness.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable, Iterable

TASK_ID = "483682b75e12"
EXPECTED_SOURCE_SHA256 = "189fbe70222e7cb05feeb7114eb0ad2a3f4f557e532cf23e3ea0a8c686979f7e"
def _find_repo_root() -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "generators/483682b75e12/generator.py").is_file():
            return candidate
    raise RuntimeError("run from the packet repo or set cwd to WORK/repo")


REPO_ROOT = _find_repo_root()
TASK_ROOT = REPO_ROOT / "generators/483682b75e12"
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
Cell = tuple[int, int]


def _components(grid: Grid, *, split_colors: bool = False) -> list[list[Cell]]:
    height, width = len(grid), len(grid[0])
    foreground = {(r, c) for r in range(height) for c in range(width) if grid[r][c] not in (7, 8)}
    seen: set[Cell] = set()
    groups: list[list[Cell]] = []
    for start in sorted(foreground):
        if start in seen:
            continue
        color = grid[start[0]][start[1]]
        stack = [start]
        seen.add(start)
        cells: list[Cell] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                neighbor = (nr, nc)
                if neighbor not in foreground or neighbor in seen:
                    continue
                if split_colors and grid[nr][nc] != color:
                    continue
                seen.add(neighbor)
                stack.append(neighbor)
        groups.append(sorted(cells))
    return groups


def _render_shift(
    grid: Grid,
    *,
    split_colors: bool = False,
    distance: Callable[[Grid, list[Cell]], int],
    direction: int = -1,
) -> Grid:
    height, width = len(grid), len(grid[0])
    output = [[8 if grid[r][c] == 8 else 7 for c in range(width)] for r in range(height)]
    for cells in _components(grid, split_colors=split_colors):
        amount = distance(grid, cells)
        for r, c in cells:
            target = r + direction * amount
            if 0 <= target < height:
                output[target][c] = grid[r][c]
    return output


def _size(_grid: Grid, cells: list[Cell]) -> int:
    return len(cells)


def _height(_grid: Grid, cells: list[Cell]) -> int:
    rows = [r for r, _ in cells]
    return max(rows) - min(rows) + 1


def _width(_grid: Grid, cells: list[Cell]) -> int:
    cols = [c for _, c in cells]
    return max(cols) - min(cols) + 1


def _bbox_area(grid: Grid, cells: list[Cell]) -> int:
    return _height(grid, cells) * _width(grid, cells)


def _distinct_colors(grid: Grid, cells: list[Cell]) -> int:
    return len({grid[r][c] for r, c in cells})


def _fixed_one(_grid: Grid, _cells: list[Cell]) -> int:
    return 1


RIVALS: tuple[tuple[str, Callable[[Grid], Grid]], ...] = (
    ("fixed_one", lambda grid: _render_shift(grid, distance=_fixed_one)),
    ("bbox_height", lambda grid: _render_shift(grid, distance=_height)),
    ("bbox_width", lambda grid: _render_shift(grid, distance=_width)),
    ("bbox_area", lambda grid: _render_shift(grid, distance=_bbox_area)),
    ("distinct_color_count", lambda grid: _render_shift(grid, distance=_distinct_colors)),
    ("monochrome_component_size", lambda grid: _render_shift(grid, split_colors=True, distance=_size)),
    ("down_by_component_size", lambda grid: _render_shift(grid, distance=_size, direction=1)),
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
                sample_index = 10_000 * profile_index + 97 * int(seed) + 11
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
