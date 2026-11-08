"""Independent review oracle and curriculum probes for 0a9926d504f3.

The canonical Racket program remains the label authority.  This module is a
small, source-bound second implementation used by tests and future reviewers:
it loads canonical pairs, classifies generated textures, computes the intended
frame/cross output, and materializes three plausible shortcut rules.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "0a9926d504f3"
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME_PATH = ROOT / "shared" / "runtime"
if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

Grid = list[list[int]]
Coord = tuple[int, int]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or GENERATOR_PATH).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_0a9926d504f3_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"canonical task {TASK_ID} is absent")


def canonical_pairs() -> list[dict[str, Grid]]:
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def canonical_program() -> str:
    program = canonical().get("program_solution")
    if not isinstance(program, str) or not program.strip():
        raise ValueError("canonical task has no executable program_solution")
    return program


def normalized_grid(grid: Iterable[Iterable[int]]) -> Grid:
    if isinstance(grid, (str, bytes)):
        raise ValueError("grid must be a sequence of rows")
    try:
        out = [list(row) for row in grid]
    except (TypeError, ValueError) as exc:
        raise ValueError("grid must be iterable") from exc
    if not out or not out[0] or any(len(row) != len(out[0]) for row in out):
        raise ValueError("grid must be nonempty and rectangular")
    for row in out:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                raise ValueError("ARC cells must be integer colors 0..9")
    return out


def nonzero_cells(grid: Iterable[Iterable[int]]) -> list[tuple[int, int, int]]:
    source = normalized_grid(grid)
    return [
        (r, c, value)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value != 0
    ]


def analyze(grid: Iterable[Iterable[int]]) -> dict[str, Any]:
    source = normalized_grid(grid)
    cells = nonzero_cells(source)
    centers = [(r, c) for r, c, value in cells if value == 2]
    if len(centers) != 1:
        raise ValueError(f"expected exactly one color-2 center, found {len(centers)}")
    others = [(r, c) for r, c, value in cells if value != 2]
    if not others:
        raise ValueError("expected at least one non-center marker")
    center = centers[0]
    # Row-major ordering intentionally mirrors grid-positions + pick-min/max.
    top = min(others, key=lambda p: p[0])
    bottom = max(others, key=lambda p: p[0])
    left = min(others, key=lambda p: p[1])
    right = max(others, key=lambda p: p[1])
    tr, br, lc, rc = top[0], bottom[0], left[1], right[1]
    return {
        "grid": source,
        "center": center,
        "others": others,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "top_row": tr,
        "bottom_row": br,
        "left_col": lc,
        "right_col": rc,
        "role_positions": {top, bottom, left, right},
        "role_candidates": {
            "top": [p for p in others if p[0] == tr],
            "bottom": [p for p in others if p[0] == br],
            "left": [p for p in others if p[1] == lc],
            "right": [p for p in others if p[1] == rc],
        },
    }


def intended_output(grid: Iterable[Iterable[int]]) -> Grid:
    info = analyze(grid)
    source: Grid = info["grid"]
    h, w = len(source), len(source[0])
    cr, cc = info["center"]
    tr, br = info["top_row"], info["bottom_row"]
    lc, rc = info["left_col"], info["right_col"]
    top_color = source[info["top"][0]][info["top"][1]]
    bottom_color = source[info["bottom"][0]][info["bottom"][1]]
    left_color = source[info["left"][0]][info["left"][1]]
    right_color = source[info["right"][0]][info["right"][1]]
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if r == tr and lc <= c <= rc:
                out[r][c] = top_color
            elif r == br and lc <= c <= rc:
                out[r][c] = bottom_color
            elif c == lc and tr <= r <= br:
                out[r][c] = left_color
            elif c == rc and tr <= r <= br:
                out[r][c] = right_color
            elif r == cr and c == cc:
                out[r][c] = 2
            elif r == cr and lc < c < rc:
                out[r][c] = 5
            elif c == cc and tr < r < br:
                out[r][c] = 5
    return out


def texture_from_grid(grid: Iterable[Iterable[int]]) -> str:
    info = analyze(grid)
    source: Grid = info["grid"]
    others: list[Coord] = info["others"]
    count = len(others)
    cr, _cc = info["center"]
    if count == 3:
        return "shared_corner"
    if count == 5:
        return "extra_marker"
    if count != 4:
        raise ValueError(f"cannot classify texture with {count} non-center markers")
    colors = [source[r][c] for r, c in others]
    if len(set(colors)) == 1:
        return "same_color"
    if cr in (info["top_row"], info["bottom_row"]):
        return "center_edge"
    return "plain"


def observed(grid: Iterable[Iterable[int]]) -> dict[str, int | str]:
    source = normalized_grid(grid)
    return {
        "grid_h": len(source),
        "grid_w": len(source[0]),
        "texture": texture_from_grid(source),
    }


def unique_extrema_roles(grid: Iterable[Iterable[int]]) -> bool:
    info = analyze(grid)
    return all(len(candidates) == 1 for candidates in info["role_candidates"].values())


def shared_corner_is_exact(grid: Iterable[Iterable[int]]) -> bool:
    try:
        info = analyze(grid)
    except ValueError:
        return False
    if len(info["others"]) != 3:
        return False
    if any(len(candidates) != 1 for candidates in info["role_candidates"].values()):
        return False
    return info["top"] == info["left"] and len(info["role_positions"]) == 3


def exactly_four_markers(grid: Iterable[Iterable[int]]) -> Grid:
    """Shortcut: solve only the canonical exactly-four-marker regime."""
    source = normalized_grid(grid)
    info = analyze(source)
    if len(info["others"]) == 4:
        return intended_output(source)
    return deepcopy(source)


def center_always_visible(grid: Iterable[Iterable[int]]) -> Grid:
    """Shortcut: let color 2 overwrite a frame edge instead of edge precedence."""
    source = normalized_grid(grid)
    out = intended_output(source)
    cr, cc = analyze(source)["center"]
    out[cr][cc] = 2
    return out


def preserve_nonrole_markers(grid: Iterable[Iterable[int]]) -> Grid:
    """Shortcut: copy any marker not selected as an extremum into the output."""
    source = normalized_grid(grid)
    info = analyze(source)
    out = intended_output(source)
    selected = set(info["role_positions"]) | {info["center"]}
    for r, c in info["others"]:
        if (r, c) not in selected:
            out[r][c] = source[r][c]
    return out


def has_shared_corner(grid: Iterable[Iterable[int]]) -> bool:
    try:
        return texture_from_grid(grid) == "shared_corner" and shared_corner_is_exact(grid)
    except ValueError:
        return False


def center_on_edge(grid: Iterable[Iterable[int]]) -> bool:
    try:
        info = analyze(grid)
    except ValueError:
        return False
    return info["center"][0] in (info["top_row"], info["bottom_row"])


def has_ignored_extra_marker(grid: Iterable[Iterable[int]]) -> bool:
    try:
        return texture_from_grid(grid) == "extra_marker"
    except ValueError:
        return False


def grid_hash(grid: Iterable[Iterable[int]]) -> str:
    payload = json.dumps(normalized_grid(grid), separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def source_sha256(path: Path = GENERATOR_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
