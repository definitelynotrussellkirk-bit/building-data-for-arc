"""Independent inspection helpers for generator review and future regressions.

This module deliberately does not import production parsing or rule helpers.  It
reconstructs panel segments, applies the documented rotation convention, and
reports the realized vote texture from returned pixels.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import os
from pathlib import Path
from typing import Iterable

HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_review_0701a2c36d45", source)
    if spec is None or spec.loader is None:
        raise ImportError(source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def rotate(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    out = normalize(cells)
    for _ in range(turns % 4):
        height = max(r for r, _ in out) + 1
        out = normalize((c, height - 1 - r) for r, c in out)
    return out


def split(grid: list[list[int]]) -> tuple[list[list[int]], list[list[list[int]]]]:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    chunks: list[list[list[int]]] = []
    start = 0
    for r, row in enumerate(grid):
        if all(value == 9 for value in row):
            chunks.append([list(x) for x in grid[start:r]])
            start = r + 1
    chunks.append([list(x) for x in grid[start:]])
    if len(chunks) != 4:
        raise ValueError(f"expected header plus three panels, got {len(chunks)} chunks")
    return chunks[0], chunks[1:]


def vote_profile(grid: list[list[int]]) -> dict[str, object]:
    header, panels = split(grid)
    if len(header) != 1 or len(panels) != 3 or any(not panel for panel in panels):
        raise ValueError("invalid header/panel structure")
    panel_h = len(panels[0])
    panel_w = len(panels[0][0])
    votes: list[set[tuple[int, int]]] = []
    for i, panel in enumerate(panels):
        cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row)
                 if value not in (0, 9)]
        votes.append(set(rotate(cells, header[0][i] - 1)))
    counts = Counter(cell for panel in votes for cell in panel)
    one = sorted(cell for cell, count in counts.items() if count == 1)
    two = sorted(cell for cell, count in counts.items() if count == 2)
    three = sorted(cell for cell, count in counts.items() if count == 3)
    if not one and not two:
        texture = "plain"
    elif len(one) == 1 and not two:
        texture = "noise_robust"
    elif not one and len(two) == 1:
        texture = "two_agree"
    elif len(one) == 1 and len(two) == 1:
        texture = "mixed_vote"
    else:
        texture = "other"
    output = [[0] * panel_w for _ in range(panel_h)]
    for (r, c), count in counts.items():
        if count >= 2 and 0 <= r < panel_h and 0 <= c < panel_w:
            output[r][c] = 8
    return {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "shape_size": min(len(panel) for panel in votes),
        "texture": texture,
        "count1": one,
        "count2": two,
        "count3": three,
        "panel_sizes": tuple(sorted(len(panel) for panel in votes)),
        "output": output,
    }


def palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})
