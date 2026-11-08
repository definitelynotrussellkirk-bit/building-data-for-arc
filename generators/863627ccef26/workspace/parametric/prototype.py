"""Native parametric family for 863627ccef26.

Both settings infer the unique D4 transform demonstrated by panels A and B and
apply it to query panel Q.  ``union_conflict_9`` is the exact selected ARC rule:
overlay Q with the transformed copy, retaining non-overlap colors and marking
collisions 9.  ``intersection_only`` is the nearby sequential variant: after
constructing the input-dependent transformed query, retain only its overlap with
Q, colored 9.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "863627ccef26"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"merge_mode": "union_conflict_9"},
    {"merge_mode": "intersection_only"},
)
TRANSFORMS = ("r1", "r2", "r3", "fh", "fv", "tr", "atr")
ALL_TRANSFORMS = ("id",) + TRANSFORMS
DEMO_SIZES = (3, 4, 5, 6, 7, 8)
QUERY_SIZES = (3, 5, 7, 9)


def _integer(value, label, low=None, high=None):
    if type(value) is not int:
        raise ValueError(f"{label} must be an exact integer")
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f"{label} must be in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"merge_mode"}:
        raise ValueError("settings must contain exactly merge_mode")
    value = settings["merge_mode"]
    if type(value) is not str or value not in {row["merge_mode"] for row in SETTINGS}:
        raise ValueError("merge_mode must be union_conflict_9 or intersection_only")
    return value


def _grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return deepcopy(grid)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def program(settings):
    name = "canonical.rkt" if _setting(settings) == "union_conflict_9" else "sequential.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _xform(grid, code):
    source = _grid(grid)
    n = len(source)
    if any(len(row) != n for row in source):
        raise ValueError("D4 transforms require a square panel")
    if code == "id":
        return source
    if code == "r1":
        return [[source[n - 1 - row][col] for row in range(n)] for col in range(n)]
    if code == "r2":
        return [row[::-1] for row in source[::-1]]
    if code == "r3":
        return [[source[row][n - 1 - col] for row in range(n)] for col in range(n)]
    if code == "fh":
        return [row[::-1] for row in source]
    if code == "fv":
        return [row[:] for row in source[::-1]]
    if code == "tr":
        return [[source[row][col] for row in range(n)] for col in range(n)]
    if code == "atr":
        return [[source[n - 1 - col][n - 1 - row] for col in range(n)] for row in range(n)]
    raise ValueError(f"unknown transform {code!r}")


def _split(grid):
    source = _grid(grid)
    size = len(source)
    if len(source[0]) != 3 * size + 2:
        raise ValueError("input must contain three square panels and two separator columns")
    if any(source[row][size] != 8 or source[row][2 * size + 1] != 8 for row in range(size)):
        raise ValueError("separator columns must be full color 8")
    panels = []
    for left in (0, size + 1, 2 * size + 2):
        panels.append([row[left:left + size] for row in source])
    if any(value in (8, 9) for panel in panels for row in panel for value in row):
        raise ValueError("panels must exclude reserved colors 8 and 9")
    return size, tuple(panels)


def _matching(a, b):
    return tuple(code for code in ALL_TRANSFORMS if _xform(a, code) == b)


def _union(query, transformed):
    size = len(query)
    return [
        [
            9 if query[row][col] and transformed[row][col]
            else query[row][col] or transformed[row][col]
            for col in range(size)
        ]
        for row in range(size)
    ]


def _intersection(query, transformed):
    size = len(query)
    return [
        [9 if query[row][col] and transformed[row][col] else 0 for col in range(size)]
        for row in range(size)
    ]


def stage_summary(grid):
    size, (panel_a, panel_b, query) = _split(grid)
    matches = _matching(panel_a, panel_b)
    if len(matches) != 1 or matches[0] == "id":
        raise ValueError(f"A-to-B transform must be unique and non-identity; matches={matches}")
    transform = matches[0]
    transformed = _xform(query, transform)
    overlap = sum(
        bool(query[row][col]) and bool(transformed[row][col])
        for row in range(size)
        for col in range(size)
    )
    carry = sum(
        bool(query[row][col]) != bool(transformed[row][col])
        for row in range(size)
        for col in range(size)
    )
    if overlap <= 0 or carry <= 0:
        raise ValueError("query must exercise both overlap and non-overlap branches")
    return {
        "panel_size": size,
        "transform": transform,
        "query": query,
        "transformed_query": transformed,
        "overlap_cells": overlap,
        "carry_cells": carry,
        "skip_a_output": [[9 if value else 0 for value in row] for row in query],
    }


def transform(grid, settings):
    mode = _setting(settings)
    summary = stage_summary(grid)
    if mode == "union_conflict_9":
        return _union(summary["query"], summary["transformed_query"])
    return _intersection(summary["query"], summary["transformed_query"])


def _rng(seed, stream, index, size):
    payload = json.dumps([seed, stream, index, size], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _neighbors(cell, size):
    row, col = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < size and 0 <= nc < size:
            yield nr, nc


def _connected_support(rng, size, count, *, anchors=()):
    support = set(anchors)
    if not support:
        support.add((rng.randrange(size), rng.randrange(size)))
    while len(support) < count:
        frontier = sorted({neighbor for cell in support for neighbor in _neighbors(cell, size)} - support)
        if not frontier:
            raise ValueError("support growth exhausted")
        support.add(rng.choice(frontier))
    return support


def _panel_from_support(size, support, *, marker_a, marker_b, fill_color):
    panel = [[0] * size for _ in range(size)]
    for row, col in support:
        panel[row][col] = fill_color
    # Two unique, differently colored adjacent markers destroy every residual
    # D4 symmetry while keeping the support connected.
    panel[0][1] = marker_a
    panel[1][0] = marker_b
    return panel


def _make_a(rng, size, target_cells):
    anchors = {(0, 0), (0, 1), (1, 0)}
    support = _connected_support(rng, size, target_cells, anchors=anchors)
    panel = _panel_from_support(size, support, marker_a=1, marker_b=2, fill_color=3)
    matches = tuple(code for code in ALL_TRANSFORMS if _xform(panel, code) == panel)
    if matches != ("id",):
        raise ValueError(f"constructed A unexpectedly symmetric: {matches}")
    return panel


def _make_q(rng, size, target_cells, code):
    anchors = {(0, 0), (0, 1), (1, 0)}
    all_cells = [(row, col) for row in range(size) for col in range(size)]
    for attempt in range(512):
        local = random.Random(rng.getrandbits(256) ^ attempt)
        support = _connected_support(local, size, target_cells, anchors=anchors)
        panel = _panel_from_support(size, support, marker_a=4, marker_b=5, fill_color=6)
        transformed = _xform(panel, code)
        overlap = sum(
            bool(panel[row][col]) and bool(transformed[row][col])
            for row, col in all_cells
        )
        if 0 < overlap < target_cells and panel != transformed:
            return panel
    raise ValueError("could not construct query with overlap and carry branches")


def sample_input(seed, stream, index, size):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(size, "panel_size", 3, 9)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be nonempty text")
    rng = _rng(seed, stream, index, size)
    offset = 0 if stream == "train" else 3
    code = TRANSFORMS[(seed + index + offset) % len(TRANSFORMS)]
    # Scale real content with panel area while retaining zeros and room for the
    # transform interaction.  9x29 reaches >70 total nonzero cells.
    target_cells = min(size * size - 3, max(5, (size * size * 2) // 5))
    panel_a = _make_a(rng, size, target_cells)
    panel_b = _xform(panel_a, code)
    query = _make_q(rng, size, target_cells, code)
    out = [[0] * (3 * size + 2) for _ in range(size)]
    for row in range(size):
        out[row][:size] = panel_a[row]
        out[row][size] = 8
        out[row][size + 1:2 * size + 1] = panel_b[row]
        out[row][2 * size + 1] = 8
        out[row][2 * size + 2:] = query[row]
    summary = stage_summary(out)
    if summary["transform"] != code:
        raise ValueError("sampler transform inference mismatch")
    if summary["skip_a_output"] == _intersection(query, summary["transformed_query"]):
        raise ValueError("Step-A ablation did not change intersection output")
    return out


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": dict(settings),
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "prototype": True,
    }
    seen = set()
    for split, sizes in (("train", DEMO_SIZES[:demos]), ("test", QUERY_SIZES[:queries])):
        for index, size in enumerate(sizes):
            grid = sample_input(seed, split, index, size)
            key = digest(grid)
            if key in seen:
                raise ValueError("episode inputs must be distinct")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
