"""Episode-fixed L-ray postprocessing family for 8a802749348c.

The byte-exact canonical setting extends every L's missing-corner diagonal.
The alternative first executes that same ray stage, then finds input-empty cells
where two same-color diagonal rays cross and marks each crossing plus its four
orthogonal neighbors with color 9.  The second step reads the ray intermediate;
without that intermediate there are no crossing cues to mark.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


TASK_ID = "8a802749348c"
HERE = Path(__file__).resolve().parent
SETTINGS = ({"postprocess": "none"}, {"postprocess": "mark_crossings"})
DEMO_SHAPES = ((13, 15), (15, 13), (16, 18), (18, 16), (20, 22), (24, 20))
QUERY_SHAPES = ((12, 16), (17, 19), (23, 25), (30, 30))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"postprocess"}:
        raise ValueError("settings must contain exactly postprocess")
    mode = value["postprocess"]
    if type(mode) is not str or mode not in {"none", "mark_crossings"}:
        raise ValueError("postprocess must be none or mark_crossings")
    return {"postprocess": mode}


def _grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid rows and colors must be exact rectangular integers 0..9")
    return value


def _canonical_program() -> str:
    root = find_root(__file__)
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row["program_solution"])
    if len(sources) != 1:
        raise RuntimeError(f"expected one exact canonical source for {TASK_ID}")
    return next(iter(sources))


CANONICAL_PROGRAM = _canonical_program()
MARK_CROSSINGS_PROGRAM = (HERE / "mark_crossings.rkt").read_text(encoding="utf-8")


def program(settings: dict[str, Any]) -> str:
    mode = _settings(settings)["postprocess"]
    return CANONICAL_PROGRAM if mode == "none" else MARK_CROSSINGS_PROGRAM


class RacketEngine:
    """Small reusable protected-Racket evaluator for focused authoring checks."""

    def __init__(self):
        self.bridge = RacketBridge()
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("a live protected Racket backend is required")
        self.identity = identity
        self._wrapped: dict[str, str] = {}
        self.evaluations = 0

    def apply(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        _grid(grid)
        wrapped = self._wrapped.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        self.evaluations += 1
        return _grid(self.bridge.eval_text(f"({wrapped} {literal})"))

    def close(self) -> None:
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _rng(seed: int, stream: str, index: int) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    _integer(index, "index", 0, 10_000)
    payload = json.dumps([TASK_ID, seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    _grid(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, sorted(cells)))
    return result


def _l_pieces(grid: list[list[int]]) -> list[dict[str, Any]]:
    pieces = []
    for color, cells in _components(grid):
        if len(cells) != 3:
            raise ValueError("every input object must be a three-cell L")
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        if (r1 - r0, c1 - c0) != (1, 1):
            raise ValueError("every input object must occupy three corners of a 2x2 box")
        box = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
        missing = list(box - set(cells))
        if len(missing) != 1:
            raise ValueError("L object must have one missing corner")
        mr, mc = missing[0]
        opposite = (r0 + r1 - mr, c0 + c1 - mc)
        pieces.append({"color": color, "cells": cells, "missing": (mr, mc),
                       "direction": (mr - opposite[0], mc - opposite[1])})
    if not pieces:
        raise ValueError("input needs at least one L")
    return pieces


def canonical_transform(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python diagnostic for the selected canonical rule."""
    _grid(grid)
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for piece in _l_pieces(grid):
        dr, dc = piece["direction"]
        rr, cc = piece["missing"][0] + dr, piece["missing"][1] + dc
        while 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = piece["color"]
            rr += dr
            cc += dc
    return out


def crossing_centers(original: list[list[int]], stage: list[list[int]] | None = None) -> list[tuple[int, int]]:
    """Cells created by the ray stage that carry both diagonal orientations."""
    _grid(original)
    stage = canonical_transform(original) if stage is None else _grid(stage)
    if (len(stage), len(stage[0])) != (len(original), len(original[0])):
        raise ValueError("stage dimensions must match input")
    found = []
    for r in range(1, len(stage) - 1):
        for c in range(1, len(stage[0]) - 1):
            value = stage[r][c]
            if (original[r][c] == 0 and value not in (0, 9)
                    and all(stage[r + dr][c + dc] == value
                            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))):
                found.append((r, c))
    return found


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _settings(settings)["postprocess"]
    stage = canonical_transform(grid)
    if mode == "none":
        return stage
    out = [row[:] for row in stage]
    for r, c in crossing_centers(grid, stage):
        for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            out[r + dr][c + dc] = 9
    return out


def _place_l(grid: list[list[int]], top: int, left: int, missing: str, color: int) -> None:
    offsets = {(0, 0), (0, 1), (1, 0), (1, 1)}
    missing_offset = {"tl": (0, 0), "tr": (0, 1), "bl": (1, 0), "br": (1, 1)}[missing]
    offsets.remove(missing_offset)
    for dr, dc in offsets:
        if grid[top + dr][left + dc] != 0:
            raise ValueError("L placement collision")
        grid[top + dr][left + dc] = color


def sample_input(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    """Construct a same-color X crossing plus short non-crossing distractor rays."""
    _integer(height, "height", 12, 30)
    _integer(width, "width", 12, 30)
    rng = _rng(seed, stream, index)
    grid = [[0] * width for _ in range(height)]

    if stream == "demo":
        offsets = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
        order_rng = _rng(seed, "demo-center-order", 0)
        order_rng.shuffle(offsets)
        offset_r, offset_c = offsets[index % len(offsets)]
    else:
        offset_r = rng.choice((-1, 0, 1))
        offset_c = rng.choice((-1, 0, 1))
    center_r = max(5, min(height - 4, height // 2 + offset_r))
    center_c = max(5, min(width - 6, width // 2 + offset_c))
    max_left_distance = min(center_r - 2, center_c - 2)
    max_right_distance = min(center_r - 2, width - center_c - 3)
    d1 = max(2, min(max_left_distance, 3 + rng.randrange(max(1, min(3, max_left_distance - 1)))))
    d2 = max(2, min(max_right_distance, 3 + rng.randrange(max(1, min(3, max_right_distance - 1)))))
    color = rng.choice(tuple(range(1, 9)))

    # Missing BR emits down-right through the selected crossing.
    _place_l(grid, center_r - d1 - 1, center_c - d1 - 1, "br", color)
    # Missing BL emits down-left through the same selected crossing.
    _place_l(grid, center_r - d2 - 1, center_c + d2, "bl", color)

    distractor_colors = [value for value in range(1, 9) if value != color]
    rng.shuffle(distractor_colors)
    if height >= 15:
        _place_l(grid, height - 3, 2, "tl", distractor_colors[0])
    if width >= 16 and height >= 16:
        _place_l(grid, height - 3, width - 4, "tr", distractor_colors[1])

    stage = canonical_transform(grid)
    centers = crossing_centers(grid, stage)
    if (center_r, center_c) not in centers:
        raise ValueError("constructed rays did not retain the intended crossing")
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    source = program(selected)
    result = {"train": [], "test": [], "program_solution": source}
    seen: set[str] = set()
    for split, profiles, count, stream in (
        ("train", DEMO_SHAPES, demos, "demo"),
        ("test", QUERY_SHAPES, queries, "query"),
    ):
        for index, (height, width) in enumerate(profiles[:count]):
            grid = sample_input(seed, stream, index, height, width)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("sampler produced a duplicate episode input")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, selected)})
    return result
