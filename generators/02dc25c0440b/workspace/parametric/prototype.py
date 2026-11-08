"""Episode-fixed mirror/postprocess family for 02dc25c0440b.

The byte-exact canonical setting mirrors every colored left-side cell across the
full-height color-9 guide.  The alternative first builds that same mirrored
intermediate and then recolors each visible right-side component by its *visible*
cell count.  Deliberately clipped source objects make this count depend on the
mirrored intermediate rather than on the original source-object size.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


TASK_ID = "02dc25c0440b"
HERE = Path(__file__).resolve().parent
SETTINGS = ({"right_label": "source_color"}, {"right_label": "visible_size"})
DEMO_SHAPES = ((11, 13), (13, 15), (15, 17), (17, 19), (20, 22), (24, 26))
QUERY_SHAPES = ((12, 14), (16, 18), (22, 24), (30, 30))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CLIPPED_DELTA_ONE = (
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)),
)
_CLIPPED_MULTI_LOSS = (
    ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"right_label"}:
        raise ValueError("settings must contain exactly right_label")
    mode = value["right_label"]
    if type(mode) is not str or mode not in {"source_color", "visible_size"}:
        raise ValueError("right_label must be source_color or visible_size")
    return {"right_label": mode}


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
VISIBLE_SIZE_PROGRAM = (HERE / "visible_size.rkt").read_text(encoding="utf-8")


def program(settings: dict[str, Any]) -> str:
    mode = _settings(settings)["right_label"]
    return CANONICAL_PROGRAM if mode == "source_color" else VISIBLE_SIZE_PROGRAM


class RacketEngine:
    """Reusable protected-Racket evaluator for focused authoring checks."""

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


def guide_col(grid: list[list[int]]) -> int:
    _grid(grid)
    candidates = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    if len(candidates) != 1:
        raise ValueError("grid must contain exactly one full-height color-9 guide")
    return candidates[0]


def _components(grid: list[list[int]], include: Callable[[int, int, int], bool]) -> list[dict[str, Any]]:
    _grid(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if (r, c) in seen or not include(r, c, color):
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
                            and grid[nr][nc] == color and include(nr, nc, color)):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": sorted(cells), "size": len(cells)})
    return result


def mirror_stage(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python diagnostic for the selected canonical rule."""
    _grid(grid)
    gc = guide_col(grid)
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(gc):
            value = grid[r][c]
            mc = 2 * gc - c
            if value not in (0, 9) and 0 <= mc < w:
                out[r][mc] = value
    return out


def right_components(stage: list[list[int]]) -> list[dict[str, Any]]:
    _grid(stage)
    gc = guide_col(stage)
    rows = _components(stage, lambda _r, c, value: c > gc and value not in (0, 9))
    return [
        {"source_color": row["color"], "cells": row["cells"], "visible_size": row["size"]}
        for row in rows
    ]


def component_correspondence(original: list[list[int]], stage: list[list[int]] | None = None) -> list[dict[str, Any]]:
    """Match each left source component to its in-bounds mirrored cells."""
    _grid(original)
    stage = mirror_stage(original) if stage is None else _grid(stage)
    if (len(stage), len(stage[0])) != (len(original), len(original[0])):
        raise ValueError("stage dimensions must match input")
    gc = guide_col(original)
    if guide_col(stage) != gc:
        raise ValueError("stage guide differs from input")
    h, w = len(original), len(original[0])
    sources = _components(original, lambda _r, c, value: c < gc and value not in (0, 9))
    visible_by_key = {
        (row["source_color"], frozenset(row["cells"])): row
        for row in right_components(stage)
    }
    result = []
    for source in sources:
        targets = sorted((r, 2 * gc - c) for r, c in source["cells"]
                         if 0 <= 2 * gc - c < w)
        if not targets:
            raise ValueError("every source component must retain at least one visible mirror cell")
        key = (source["color"], frozenset(targets))
        if key not in visible_by_key:
            raise ValueError("mirrored stage does not preserve a distinct source-colored component")
        result.append({
            "source_color": source["color"],
            "source_cells": source["cells"],
            "source_size": source["size"],
            "visible_cells": targets,
            "visible_size": len(targets),
        })
    return result


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _settings(settings)["right_label"]
    stage = mirror_stage(grid)
    if mode == "source_color":
        return stage
    out = [row[:] for row in stage]
    for component in right_components(stage):
        size = component["visible_size"]
        if not 1 <= size <= 8:
            raise ValueError("visible component size must stay in color range 1..8")
        for r, c in component["cells"]:
            out[r][c] = size
    return out


def _can_place(grid: list[list[int]], cells: list[tuple[int, int]], gc: int) -> bool:
    h, w = len(grid), len(grid[0])
    proposed = set(cells)
    if any(not (0 <= r < h and 0 <= c < gc) or grid[r][c] != 0 for r, c in cells):
        return False
    for r, c in cells:
        for dr, dc in _DIR4:
            nr, nc = r + dr, c + dc
            if (nr, nc) in proposed:
                continue
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, 9):
                return False
    return True


def _paint(grid: list[list[int]], top: int, left: int,
           shape: tuple[tuple[int, int], ...], color: int, gc: int) -> None:
    cells = [(top + dr, left + dc) for dr, dc in shape]
    if not _can_place(grid, cells, gc):
        raise ValueError("shape placement collision")
    for r, c in cells:
        grid[r][c] = color


def sample_input(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    """Construct one clipped source object plus separate fully visible distractors."""
    _integer(height, "height", 11, 30)
    _integer(width, "width", 13, 30)
    rng = _rng(seed, stream, index)
    grid = [[0] * width for _ in range(height)]

    base_gc = width // 2 + 1
    max_extra = max(0, min(2, width - 4 - base_gc))
    gc = base_gc + rng.randint(0, max_extra)
    for row in grid:
        row[gc] = 9

    # c == boundary clips while c > boundary remains visible.  The first two
    # demonstrations deliberately use different clipping losses: one cell, then
    # multiple cells.  This defeats fixed-label and source-size-minus-one shortcuts.
    boundary = 2 * gc - width
    if stream == "demo" and index == 0:
        clipped_shape = rng.choice(_CLIPPED_DELTA_ONE)
    elif stream == "demo" and index == 1:
        clipped_shape = rng.choice(_CLIPPED_MULTI_LOSS)
    else:
        clipped_shape = rng.choice(_CLIPPED_DELTA_ONE + _CLIPPED_MULTI_LOSS)
    clipped_height = max(r for r, _ in clipped_shape) + 1
    clipped_top = rng.randint(1, height - clipped_height - 1)
    source_size = len(clipped_shape)
    visible_size = sum(1 for _r, c in clipped_shape if c > 0)
    clipped_colors = [color for color in range(1, 9)
                      if color not in {source_size, visible_size}]
    clipped_color = rng.choice(clipped_colors)
    _paint(grid, clipped_top, boundary, clipped_shape, clipped_color, gc)

    distractor_shapes = (
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    )
    distractor_colors = [1, 2, 5, 6, 7, 8]
    rng.shuffle(distractor_colors)
    desired = 1 + rng.randrange(2)
    placed = 0
    for attempt in range(80):
        if placed >= desired:
            break
        shape = distractor_shapes[(attempt + rng.randrange(len(distractor_shapes))) % len(distractor_shapes)]
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        left_lo = max(boundary + 4, gc - 6)
        left_hi = gc - sw - 1
        if left_lo > left_hi:
            continue
        top = rng.randint(0, height - sh)
        left = rng.randint(left_lo, left_hi)
        cells = [(top + dr, left + dc) for dr, dc in shape]
        if not _can_place(grid, cells, gc):
            continue
        visible_size = len(shape)
        choices = [color for color in distractor_colors if color != visible_size]
        color = choices[placed % len(choices)]
        _paint(grid, top, left, shape, color, gc)
        placed += 1
    if placed == 0:
        fallback = ((0, 0), (1, 0), (2, 0))
        for top in range(0, height - 2):
            left = gc - 3
            cells = [(top + dr, left + dc) for dr, dc in fallback]
            if _can_place(grid, cells, gc):
                _paint(grid, top, left, fallback, 5, gc)
                placed = 1
                break
    if placed == 0:
        raise ValueError("failed to place a visible distractor")

    correspondence = component_correspondence(grid, mirror_stage(grid))
    if not any(row["visible_size"] < row["source_size"] for row in correspondence):
        raise ValueError("constructed input lost its partial clipping witness")
    if any(row["source_color"] == row["visible_size"] for row in correspondence):
        raise ValueError("source colors must not reveal visible-size labels")
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
