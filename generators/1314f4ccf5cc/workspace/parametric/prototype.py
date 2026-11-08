"""Matched-input cardinal-plus versus diagonal-X completion episodes.

Python labels are claims until the protected Racket worker executes them.  The
input sampler is independent of the private episode setting and of query count.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "1314f4ccf5cc"
SETTINGS = ({"footprint": "cardinal"}, {"footprint": "diagonal"})

_CARDINAL = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))

# The base two-yellow motif has one unique interpretation under each footprint:
# cardinal center=(1,1), diagonal center=(1,2).  The union is gray/yellow, so
# both programs receive exactly the same lawful evidence and disagree only on
# which gray cells complete the hidden shape.
_BASE_YELLOW = {(0, 1), (1, 2)}
_BASE_CARDINAL = {(1 + dr, 1 + dc) for dr, dc in _CARDINAL}
_BASE_DIAGONAL = {(1 + dr, 2 + dc) for dr, dc in _DIAGONAL}
_BASE_UNION = _BASE_CARDINAL | _BASE_DIAGONAL

_DEMOS = (
    (10, 12, 2, 0.18),
    (12, 14, 3, 0.22),
    (14, 16, 3, 0.27),
    (16, 18, 4, 0.31),
    (18, 20, 4, 0.35),
    (20, 22, 5, 0.38),
)
_QUERIES = (
    (11, 13, 2, 0.20),
    (17, 19, 4, 0.29),
    (24, 26, 6, 0.34),
    (30, 30, 8, 0.38),
)
_TARGETS = (
    (0.08, 0.08), (0.08, 0.92), (0.92, 0.08), (0.92, 0.92),
    (0.50, 0.50), (0.08, 0.50), (0.92, 0.50), (0.50, 0.08),
    (0.50, 0.92),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"footprint"}
        or type(settings["footprint"]) is not str
        or settings["footprint"] not in ("cardinal", "diagonal")
    ):
        raise ValueError(
            "settings must be exactly {'footprint': 'cardinal'|'diagonal'}"
        )
    return settings["footprint"]


def program(settings):
    footprint = _setting(settings)
    return (HERE / ("canonical.rkt" if footprint == "cardinal" else "diagonal.rkt")).read_text()


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _rotate(cells):
    return {(c, -r) for r, c in cells}


def _normalize(*groups):
    all_cells = set().union(*groups)
    min_r = min(r for r, _ in all_cells)
    min_c = min(c for _, c in all_cells)
    return tuple({(r - min_r, c - min_c) for r, c in group} for group in groups)


def _motif(rotation):
    yellow = set(_BASE_YELLOW)
    cardinal = set(_BASE_CARDINAL)
    diagonal = set(_BASE_DIAGONAL)
    for _ in range(rotation % 4):
        yellow, cardinal, diagonal = map(_rotate, (yellow, cardinal, diagonal))
    yellow, cardinal, diagonal = _normalize(yellow, cardinal, diagonal)
    union = cardinal | diagonal
    height = max(r for r, _ in union) + 1
    width = max(c for _, c in union) + 1
    return yellow, cardinal, diagonal, union, height, width


def _translated(cells, top, left):
    return {(top + r, left + c) for r, c in cells}


def _far_enough(cells, existing, gap=3):
    return all(max(abs(r - rr), abs(c - cc)) >= gap for r, c in cells for rr, cc in existing)


def _place_motifs(height, width, count, rng, phase):
    colored = set()
    yellow_all = set()
    motifs = []
    for index in range(count):
        rotation = (phase + index) % 4
        yellow, cardinal, diagonal, union, mh, mw = _motif(rotation)
        candidates = []
        target_r, target_c = _TARGETS[index]
        # Keep the complete radius-one footprints away from the boundary.
        # A clipped edge footprint can otherwise mimic the same yellow fragment
        # with fewer gray cells, creating a second lawful interpretation.
        for top in range(1, height - mh):
            for left in range(1, width - mw):
                placed_union = _translated(union, top, left)
                placed_yellow = _translated(yellow, top, left)
                if placed_union & colored or not _far_enough(placed_yellow, yellow_all):
                    continue
                center_r = top + (mh - 1) / 2
                center_c = left + (mw - 1) / 2
                score = (
                    center_r - target_r * (height - 1)
                ) ** 2 + (
                    center_c - target_c * (width - 1)
                ) ** 2
                candidates.append((score, rng.random(), top, left))
        if not candidates:
            raise ValueError("unable to place separated matched completion motifs")
        _score, _tie, top, left = min(candidates)
        placed = {
            "yellow": _translated(yellow, top, left),
            "cardinal": _translated(cardinal, top, left),
            "diagonal": _translated(diagonal, top, left),
            "union": _translated(union, top, left),
        }
        colored |= placed["union"]
        yellow_all |= placed["yellow"]
        motifs.append(placed)
    return motifs, colored, yellow_all


def _components_8(cells):
    remaining = set(cells)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = [start]
        component = {start}
        while queue:
            row, col = queue.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    neighbor = (row + dr, col + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
        components.append(component)
    return components


def _footprint(center, offsets, height, width):
    row, col = center
    return {
        (row + dr, col + dc)
        for dr, dc in offsets
        if 0 <= row + dr < height and 0 <= col + dc < width
    }


def _candidates(grid, component, offsets):
    height, width = len(grid), len(grid[0])
    candidates = []
    for row in range(height):
        for col in range(width):
            footprint = _footprint((row, col), offsets, height, width)
            yellow = {cell for cell in footprint if grid[cell[0]][cell[1]] == 4}
            gray = {cell for cell in footprint if grid[cell[0]][cell[1]] == 5}
            if yellow == component and gray and all(grid[r][c] in (4, 5) for r, c in footprint):
                candidates.append((row, col, gray))
    return candidates


def _validate_dual(grid):
    yellow = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    components = _components_8(yellow)
    if not components:
        raise ValueError("matched scene needs at least one yellow fragment")
    for component in components:
        for name, offsets in (("cardinal", _CARDINAL), ("diagonal", _DIAGONAL)):
            candidates = _candidates(grid, component, offsets)
            if len(candidates) != 1:
                raise ValueError(
                    f"yellow fragment must have one {name} interpretation, got {len(candidates)}"
                )


def sample_input(seed, index, *, split):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    specs = _DEMOS if split == "train" else _QUERIES
    _integer(index, 0, len(specs) - 1, "index")
    height, width, count, density = specs[index]
    rng = _rng(seed, split, index)
    motifs, colored, yellow = _place_motifs(height, width, count, rng, seed % 4 + index)

    grid = [[0] * width for _ in range(height)]
    for row, col in colored:
        grid[row][col] = 5
    for row, col in yellow:
        grid[row][col] = 4

    # Gray camouflage stays outside every radius-two yellow neighborhood, so it
    # cannot create an alternative five-cell interpretation for either rule.
    guarded = {
        (r, c)
        for yr, yc in yellow
        for r in range(max(0, yr - 2), min(height, yr + 3))
        for c in range(max(0, yc - 2), min(width, yc + 3))
    }
    available = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in colored and (r, c) not in guarded
    ]
    rng.shuffle(available)
    target_nonzero = min(height * width - 2, max(len(colored) + 1, round(density * height * width)))
    for row, col in available[: max(0, target_nonzero - len(colored))]:
        grid[row][col] = 5

    _validate_dual(grid)
    # Both hidden rules must be behaviorally distinguishable on every pair.
    if claimed_output(grid, SETTINGS[0]) == claimed_output(grid, SETTINGS[1]):
        raise ValueError("matched scene failed to distinguish the two footprints")
    return grid


def claimed_output(grid, settings):
    footprint = _setting(settings)
    offsets = _CARDINAL if footprint == "cardinal" else _DIAGONAL
    output = deepcopy(grid)
    yellow = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    for component in _components_8(yellow):
        candidates = _candidates(grid, component, offsets)
        if len(candidates) != 1:
            raise ValueError(f"scene is not uniquely interpretable as {footprint}")
        for row, col in candidates[0][2]:
            output[row][col] = 2
    return output


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, index, split=split)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": claimed_output(grid, settings)})
    result["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return result
