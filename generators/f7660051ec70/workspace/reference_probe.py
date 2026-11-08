"""Independent review oracle for f7660051ec70.

This helper parses color-1 rectangular frames directly from pixels and mirrors
three candidate rules.  It is test tooling only; the canonical Racket program
remains the label authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "f7660051ec70"


def root() -> Path:
    return Path(find_root(__file__))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or root() / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=root(), labeled_only=True)


def _normal_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    rows = [list(row) for row in grid]
    if not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int for row in rows for v in row):
        raise ValueError("grid cells must be integers")
    return rows


def frames(grid: Any) -> list[dict[str, int]]:
    """Return exact 4-connected color-1 rectangular outlines."""
    g = _normal_grid(grid)
    height, width = len(g), len(g[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, int]] = []
    for sr in range(height):
        for sc in range(width):
            if g[sr][sc] != 1 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and g[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            expected = (
                {(r1, c) for c in range(c1, c2 + 1)}
                | {(r2, c) for c in range(c1, c2 + 1)}
                | {(r, c1) for r in range(r1, r2 + 1)}
                | {(r, c2) for r in range(r1, r2 + 1)}
            )
            if cells != expected or r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
                raise ValueError("color-1 component is not one rectangular frame")
            seed_count = sum(
                g[r][c] == 2
                for r in range(r1 + 1, r2)
                for c in range(c1 + 1, c2)
            )
            result.append(
                {
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "seed_count": seed_count,
                }
            )
    return sorted(result, key=lambda item: (item["r1"], item["c1"]))


def _fill(grid: Any, mode: str) -> list[list[int]]:
    g = _normal_grid(grid)
    out = deepcopy(g)
    for frame in frames(g):
        seeds = frame["seed_count"]
        fill = {
            "intended": seeds >= 1,
            "exactly_one": seeds == 1,
            "all_frames": True,
        }[mode]
        if not fill:
            continue
        for r in range(frame["r1"] + 1, frame["r2"]):
            for c in range(frame["c1"] + 1, frame["c2"]):
                if out[r][c] == 0:
                    out[r][c] = 3
    return out


def intended_output(grid: Any) -> list[list[int]]:
    return _fill(grid, "intended")


def exactly_one_output(grid: Any) -> list[list[int]]:
    return _fill(grid, "exactly_one")


def fill_all_output(grid: Any) -> list[list[int]]:
    return _fill(grid, "all_frames")


def observed(grid: Any) -> dict[str, Any]:
    g = _normal_grid(grid)
    parsed = frames(g)
    seeded = [f for f in parsed if f["seed_count"]]
    decoys = [f for f in parsed if not f["seed_count"]]
    counts = {f["seed_count"] for f in seeded}
    return {
        "grid_h": len(g),
        "grid_w": len(g[0]),
        "n_seeded_frames": len(seeded),
        "n_decoy_frames": len(decoys),
        "seed_count": next(iter(counts)) if len(counts) == 1 else "mixed",
    }
